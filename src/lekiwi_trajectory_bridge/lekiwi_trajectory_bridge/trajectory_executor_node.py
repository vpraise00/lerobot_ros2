from __future__ import annotations

from typing import List, Sequence, Tuple
import time

import rclpy
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import QoSPresetProfiles, QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectoryPoint


class TrajectoryExecutor(Node):
    """Streams FollowJointTrajectory goals to Isaac Sim via JointState commands."""

    def __init__(self) -> None:
        super().__init__("lekiwi_arm_trajectory_executor")

        self.declare_parameter(
            "joint_names",
            [
                "STS3215_03a_v1_Revolute_45",
                "STS3215_03a_v1_1_Revolute_49",
                "STS3215_03a_v1_2_Revolute_51",
                "STS3215_03a_v1_3_Revolute_53",
                "STS3215_03a_Wrist_Roll_v1_Revolute_55",
                "STS3215_03a_v1_4_Revolute_57",
            ],
        )
        self.declare_parameter("action_name", "/lekiwi_arm_controller/follow_joint_trajectory")
        self.declare_parameter("output_topic", "/joint_command")
        self.declare_parameter("publish_rate_hz", 200.0)
        self.declare_parameter("goal_tolerance", 0.01)

        self._joint_names = list(self.get_parameter("joint_names").get_parameter_value().string_array_value)
        self._action_name = self.get_parameter("action_name").get_parameter_value().string_value
        self._output_topic = self.get_parameter("output_topic").get_parameter_value().string_value
        self._publish_rate = max(10.0, float(self.get_parameter("publish_rate_hz").value))
        self._goal_tolerance = float(self.get_parameter("goal_tolerance").value)

        self._current_positions = [0.0 for _ in self._joint_names]
        self._last_goal_mapping: List[int] | None = None  # incoming joint order → executor order
        qos = QoSProfile(depth=10)
        qos.reliability = QoSReliabilityPolicy.RELIABLE
        qos.history = QoSHistoryPolicy.KEEP_LAST
        self._publisher = self.create_publisher(JointState, self._output_topic, qos)
        self._action_server = ActionServer(
            self,
            FollowJointTrajectory,
            self._action_name,
            goal_callback=self._goal_callback,
            cancel_callback=self._cancel_callback,
            execute_callback=self._execute_callback,
        )

        self.get_logger().info(
            "LeKiwi arm trajectory executor ready\n"
            f"  action: {self._action_name}\n"
            f"  output_topic: {self._output_topic}\n"
            f"  joints: {self._joint_names}"
        )

    def destroy_node(self) -> bool:
        self._action_server.destroy()
        return super().destroy_node()

    def _goal_callback(self, goal: FollowJointTrajectory.Goal) -> GoalResponse:
        if not goal.trajectory.points:
            self.get_logger().warning("Rejecting trajectory goal with no points")
            return GoalResponse.REJECT
        incoming = list(goal.trajectory.joint_names)
        if set(incoming) != set(self._joint_names):
            self.get_logger().warning("Rejecting trajectory goal with mismatched joint set.")
            return GoalResponse.REJECT
        # Build mapping once per goal; reorder points later
        self._last_goal_mapping = [incoming.index(jn) for jn in self._joint_names]
        return GoalResponse.ACCEPT

    def _cancel_callback(self, _goal_handle) -> CancelResponse:
        self.get_logger().info("Received cancel request for trajectory goal.")
        return CancelResponse.ACCEPT

    def _execute_callback(self, goal_handle) -> FollowJointTrajectory.Result:
        goal = goal_handle.request
        traj_points = self._prepare_points(goal.trajectory.points)
        publish_period = 1.0 / self._publish_rate

        total_time = traj_points[-1].time_from_start

        feedback = FollowJointTrajectory.Feedback()
        feedback.joint_names = list(self._joint_names)

        t = 0.0
        while t <= total_time + 1e-6:
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                result = FollowJointTrajectory.Result()
                result.error_code = FollowJointTrajectory.Result.PATH_TOLERANCE_VIOLATED
                result.error_string = "Trajectory canceled by client."
                return result

            positions, velocities = self._sample(traj_points, t)
            self._publish_joint_state(positions, velocities)

            desired_point = JointTrajectoryPoint()
            desired_point.positions = list(positions)
            desired_point.velocities = list(velocities)
            desired_point.time_from_start = Duration(seconds=t).to_msg()
            feedback.desired = desired_point
            feedback.actual = desired_point
            feedback.error = JointTrajectoryPoint()
            goal_handle.publish_feedback(feedback)

            time.sleep(publish_period)
            t += publish_period

        # Final point to make sure we exactly match goal
        final_positions, final_velocities = self._sample(traj_points, total_time)
        self._publish_joint_state(final_positions, final_velocities)
        last_error = max(abs(fp - gp) for fp, gp in zip(final_positions, traj_points[-1].positions))

        result = FollowJointTrajectory.Result()
        if last_error > self._goal_tolerance:
            goal_handle.abort()
            result.error_code = FollowJointTrajectory.Result.GOAL_TOLERANCE_VIOLATED
            result.error_string = f"Final error {last_error:.4f} exceeded tolerance {self._goal_tolerance}"
        else:
            goal_handle.succeed()
            result.error_code = FollowJointTrajectory.Result.SUCCESSFUL
        return result

    def _publish_joint_state(self, positions: Sequence[float], velocities: Sequence[float]) -> None:
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = list(self._joint_names)
        msg.position = list(positions)
        msg.velocity = list(velocities)
        self._current_positions = list(positions)
        self._publisher.publish(msg)

    def _prepare_points(self, points: Sequence[JointTrajectoryPoint]) -> List[_TrajectoryPoint]:
        prepared: List[_TrajectoryPoint] = []
        last_time = 0.0
        for idx, pt in enumerate(points):
            t = float(pt.time_from_start.sec) + float(pt.time_from_start.nanosec) * 1e-9
            if idx == 0 and t > 1e-6:
                prepared.append(
                    _TrajectoryPoint(
                        time_from_start=0.0,
                        positions=list(self._current_positions),
                        velocities=[0.0 for _ in self._joint_names],
                    )
                )
            if t <= last_time:
                t = last_time + 1e-4
            last_time = t
            prepared.append(
                _TrajectoryPoint(
                    time_from_start=t,
                    positions=self._remap(_ensure_length(pt.positions, self._joint_names, self._current_positions)),
                    velocities=self._remap(_ensure_length(pt.velocities, self._joint_names, None)),
                )
            )

        if not prepared:
            raise ValueError("Trajectory must contain at least one point.")
        return prepared

    def _remap(self, values: Sequence[float] | None) -> List[float]:
        """Reorder incoming values into the executor's joint order using the last goal mapping."""
        if values is None:
            return [0.0 for _ in self._joint_names]
        if self._last_goal_mapping is None:
            return list(values)
        return [values[i] for i in self._last_goal_mapping]

    def _sample(self, points: Sequence[_TrajectoryPoint], current_time: float) -> Tuple[List[float], List[float]]:
        if current_time <= points[0].time_from_start:
            return list(points[0].positions), list(points[0].velocities or [0.0] * len(self._joint_names))

        for idx in range(1, len(points)):
            prev_pt = points[idx - 1]
            next_pt = points[idx]
            if current_time <= next_pt.time_from_start:
                span = max(next_pt.time_from_start - prev_pt.time_from_start, 1e-5)
                ratio = (current_time - prev_pt.time_from_start) / span
                positions = [
                    prev_pt.positions[j] + ratio * (next_pt.positions[j] - prev_pt.positions[j])
                    for j in range(len(self._joint_names))
                ]
                velocities = self._interpolate_velocities(prev_pt, next_pt, ratio, span)
                return positions, velocities

        last = points[-1]
        velocities = last.velocities or [0.0] * len(self._joint_names)
        return list(last.positions), list(velocities)

    def _interpolate_velocities(
        self, prev_pt: "_TrajectoryPoint", next_pt: "_TrajectoryPoint", ratio: float, span: float
    ) -> List[float]:
        if prev_pt.velocities and next_pt.velocities:
            return [
                prev_pt.velocities[j] + ratio * (next_pt.velocities[j] - prev_pt.velocities[j])
                for j in range(len(self._joint_names))
            ]
        if next_pt.velocities:
            return list(next_pt.velocities)
        if prev_pt.velocities:
            return list(prev_pt.velocities)
        return [
            (next_pt.positions[j] - prev_pt.positions[j]) / span for j in range(len(self._joint_names))
        ]


class _TrajectoryPoint:
    __slots__ = ("time_from_start", "positions", "velocities")

    def __init__(self, time_from_start: float, positions: List[float], velocities: List[float] | None) -> None:
        self.time_from_start = time_from_start
        self.positions = positions
        self.velocities = velocities


def _ensure_length(
    values: Sequence[float], joint_names: Sequence[str], fallback: Sequence[float] | None
) -> List[float]:
    if values and len(values) == len(joint_names):
        return [float(v) for v in values]
    if fallback is not None:
        return [float(v) for v in fallback]
    return [0.0 for _ in joint_names]


def main() -> None:
    rclpy.init()
    node = TrajectoryExecutor()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
