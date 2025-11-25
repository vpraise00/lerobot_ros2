from __future__ import annotations

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from moveit_msgs.msg import PlanningScene
from sensor_msgs.msg import JointState
from std_msgs.msg import Header


class PlanningSceneQoSBridge(Node):
    """
    Subscribes to /monitored_planning_scene with the publisher's QoS (volatile)
    and republishes it on the same topic with transient_local durability so RViz
    (which expects latched planning scene) can receive it.
    - Also listens to /planning_scene (world updates) and republishes it.
    - Fallback: if no scene ever arrives, publishes a minimal PlanningScene that
      only carries the latest /joint_states so RViz/MoveIt initialize.
    """

    def __init__(self) -> None:
        super().__init__("planning_scene_qos_bridge")
        self._last_scene: PlanningScene | None = None
        self._last_joint_state: JointState | None = None
        self._fallback_published = False

        # Match publisher QoS (volatile, reliable)
        sub_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
        )
        # Republish with transient_local so late-joining subscribers get the last scene
        pub_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
        )

        self._pub = self.create_publisher(PlanningScene, "/monitored_planning_scene", pub_qos)
        self._sub = self.create_subscription(PlanningScene, "/monitored_planning_scene", self._cb, sub_qos)
        self._ps_sub = self.create_subscription(PlanningScene, "/planning_scene", self._cb, sub_qos)
        self._js_sub = self.create_subscription(JointState, "/joint_states", self._cb_joint_state, sub_qos)
        self._republish_timer = self.create_timer(1.0, self._republish_last)
        self._fallback_timer = self.create_timer(5.0, self._publish_fallback_if_needed)
        self.get_logger().info("Planning scene QoS bridge ready (volatile -> transient_local).")

    def _cb(self, msg: PlanningScene) -> None:
        self._last_scene = msg
        self._pub.publish(msg)

    def _cb_joint_state(self, msg: JointState) -> None:
        self._last_joint_state = msg

    def _republish_last(self) -> None:
        if self._last_scene is not None:
            self._pub.publish(self._last_scene)

    def _publish_fallback_if_needed(self) -> None:
        if self._last_scene is not None or self._fallback_published is True:
            return
        if self._last_joint_state is None:
            return
        # Build a minimal PlanningScene with the latest joint states
        ps = PlanningScene()
        ps.scene_name = "lekiwi_minimal"
        ps.is_diff = False
        # Ensure header.stamp is filled to avoid stale-check in consumers
        js = JointState()
        js.header = Header()
        js.header.stamp = self.get_clock().now().to_msg()
        js.name = list(self._last_joint_state.name)
        js.position = list(self._last_joint_state.position)
        js.velocity = list(self._last_joint_state.velocity)
        js.effort = list(self._last_joint_state.effort)
        ps.robot_state.joint_state = js
        self._last_scene = ps
        self._pub.publish(ps)
        self._fallback_published = True
        self.get_logger().warn("No planning scene received; publishing fallback scene with joint_states only.")

    def request_initial_scene_blocking(self, service_wait: float = 5.0, call_timeout: float = 30.0) -> None:
        tries = 0
        while True:
            tries += 1
            if not self._ps_client.wait_for_service(timeout_sec=service_wait):
                self.get_logger().warn("Service /get_planning_scene not available yet; retrying...")
                continue
            req = GetPlanningScene.Request()
            try:
                future = self._ps_client.call_async(req)
                rclpy.spin_until_future_complete(self, future, timeout_sec=call_timeout)
                if future.result():
                    scene = future.result().scene
                    self._last_scene = scene
                    self._pub.publish(scene)
                    self.get_logger().info("Initial planning scene pulled from /get_planning_scene and republished.")
                    return
                else:
                    self.get_logger().warn("Empty response from /get_planning_scene; retrying...")
            except Exception as exc:
                self.get_logger().warn(f"Failed to call /get_planning_scene: {exc}; retrying...")


def main() -> None:
    rclpy.init()
    node = PlanningSceneQoSBridge()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
