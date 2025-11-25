from __future__ import annotations

import math
from typing import List

import rclpy
from geometry_msgs.msg import Twist, TransformStamped, Quaternion
from nav_msgs.msg import Odometry
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import QoSPresetProfiles
from sensor_msgs.msg import JointState
from tf2_ros import TransformBroadcaster


def _load_float_list(values: List[float]) -> List[float]:
    return [float(v) for v in values]


def _wrap_angle(angle: float) -> float:
    """Wrap angle to [-pi, pi] range to avoid PhysX ±2π limit."""
    return math.atan2(math.sin(angle), math.cos(angle))


class KiwiBaseController(Node):
    """Converts /cmd_vel into wheel joint commands for the Kiwi base."""

    def __init__(self) -> None:
        super().__init__("lekiwi_kiwi_base_controller")

        self.declare_parameter("input_topic", "/cmd_vel")
        self.declare_parameter("output_topic", "/joint_command")
        self.declare_parameter(
            "joint_names",
            [
                "ST3215_Servo_Motor_v1_2_Revolute_60",
                "ST3215_Servo_Motor_v1_1_Revolute_62",
                "ST3215_Servo_Motor_v1_Revolute_64",
            ],
        )
        self.declare_parameter("wheel_angles_deg", [0.0, 120.0, 240.0])
        self.declare_parameter("wheel_radius", 0.055)
        self.declare_parameter("base_radius", 0.25)
        self.declare_parameter("publish_rate_hz", 100.0)
        self.declare_parameter("command_timeout", 0.5)
        self.declare_parameter("max_wheel_speed", 25.0)

        self._input_topic: str = self.get_parameter("input_topic").get_parameter_value().string_value
        self._output_topic: str = self.get_parameter("output_topic").get_parameter_value().string_value
        self._joint_names: List[str] = list(self.get_parameter("joint_names").get_parameter_value().string_array_value)
        self._wheel_angles = [
            math.radians(angle) for angle in _load_float_list(self.get_parameter("wheel_angles_deg").value)
        ]
        self._wheel_radius = float(self.get_parameter("wheel_radius").value)
        self._base_radius = float(self.get_parameter("base_radius").value)
        self._publish_rate = float(self.get_parameter("publish_rate_hz").value)
        self._timeout = Duration(seconds=float(self.get_parameter("command_timeout").value))
        self._max_wheel_speed = abs(float(self.get_parameter("max_wheel_speed").value))

        if len(self._joint_names) != 3 or len(self._wheel_angles) != 3:
            raise ValueError("Kiwi base controller expects exactly 3 joint names and wheel angles.")

        self._last_cmd_time = self.get_clock().now()
        self._last_publish_time = None
        self._last_cmd = Twist()
        self._wheel_positions = [0.0, 0.0, 0.0]

        # Odometry state
        self._odom_x = 0.0
        self._odom_y = 0.0
        self._odom_theta = 0.0
        self._odom_vx = 0.0
        self._odom_vy = 0.0
        self._odom_omega = 0.0
        self._odom_time = self.get_clock().now()

        # Latest wheel velocities from joint_states feedback
        self._actual_wheel_velocities = [0.0, 0.0, 0.0]

        cmd_qos = QoSPresetProfiles.SENSOR_DATA.value
        js_qos = QoSPresetProfiles.SYSTEM_DEFAULT.value

        # Subscribe to cmd_vel commands
        self._cmd_sub = self.create_subscription(Twist, self._input_topic, self._cmd_callback, cmd_qos)

        # Subscribe to joint_states for odometry computation
        self._joint_state_sub = self.create_subscription(
            JointState, '/joint_states', self._joint_state_callback, js_qos
        )

        # Publish joint commands
        self._js_pub = self.create_publisher(JointState, self._output_topic, js_qos)

        # Publish odometry
        self._odom_pub = self.create_publisher(Odometry, '/odom', js_qos)

        # TF broadcaster
        self._tf_broadcaster = TransformBroadcaster(self)

        self._timer = self.create_timer(1.0 / self._publish_rate, self._on_timer)

        self.get_logger().info(
            "LeKiwi Kiwi base controller ready\n"
            f"  input topic:  {self._input_topic}\n"
            f"  output topic: {self._output_topic}\n"
            f"  joints: {self._joint_names}"
        )

    def _cmd_callback(self, msg: Twist) -> None:
        self._last_cmd = msg
        self._last_cmd_time = self.get_clock().now()

    def _joint_state_callback(self, msg: JointState) -> None:
        """Extract wheel velocities from joint_states for odometry computation."""
        for idx, joint_name in enumerate(self._joint_names):
            if joint_name in msg.name:
                js_idx = msg.name.index(joint_name)
                if js_idx < len(msg.velocity):
                    self._actual_wheel_velocities[idx] = msg.velocity[js_idx]

    def _on_timer(self) -> None:
        now = self.get_clock().now()
        if now - self._last_cmd_time > self._timeout:
            cmd = Twist()
        else:
            cmd = self._last_cmd

        vx = cmd.linear.x
        vy = cmd.linear.y
        omega = cmd.angular.z

        wheel_speeds = self._compute_wheel_speeds(vx, vy, omega)
        dt = 0.0
        if self._last_publish_time is not None:
            dt = (now - self._last_publish_time).nanoseconds * 1e-9
        self._last_publish_time = now

        # For continuous wheel joints, use velocity control only (no position)
        # Position control causes PhysX ±2π limit errors
        msg = JointState()
        msg.header.stamp = now.to_msg()
        msg.name = self._joint_names
        msg.position = []  # Empty - velocity control only
        msg.velocity = wheel_speeds

        self._js_pub.publish(msg)

        # Update and publish odometry
        odom_dt = (now - self._odom_time).nanoseconds * 1e-9
        if odom_dt > 0.0:
            self._update_odometry(odom_dt)
            self._odom_time = now
        self._publish_odometry(now.to_msg())

    def _compute_wheel_speeds(self, vx: float, vy: float, omega: float) -> List[float]:
        """Inverse kinematics: base velocity → wheel velocities."""
        speeds: List[float] = []
        for theta in self._wheel_angles:
            speed = (1.0 / self._wheel_radius) * (-math.sin(theta) * vx + math.cos(theta) * vy + self._base_radius * omega)
            speed = max(min(speed, self._max_wheel_speed), -self._max_wheel_speed)
            speeds.append(speed)
        return speeds

    def _compute_base_velocity(self, wheel_speeds: List[float]) -> tuple[float, float, float]:
        """Forward kinematics: wheel velocities → base velocity (vx, vy, omega)."""
        # Kiwi drive forward kinematics (Moore-Penrose pseudoinverse)
        # v_x = r/3 * (-sin(0°)*w0 - sin(120°)*w1 - sin(240°)*w2)
        # v_y = r/3 * (cos(0°)*w0 + cos(120°)*w1 + cos(240°)*w2)
        # omega = r/(3*R) * (w0 + w1 + w2)

        r = self._wheel_radius
        R = self._base_radius

        w0, w1, w2 = wheel_speeds

        vx = (r / 3.0) * (
            -math.sin(self._wheel_angles[0]) * w0
            - math.sin(self._wheel_angles[1]) * w1
            - math.sin(self._wheel_angles[2]) * w2
        )

        vy = (r / 3.0) * (
            math.cos(self._wheel_angles[0]) * w0
            + math.cos(self._wheel_angles[1]) * w1
            + math.cos(self._wheel_angles[2]) * w2
        )

        omega = (r / (3.0 * R)) * (w0 + w1 + w2)

        return vx, vy, omega

    def _update_odometry(self, dt: float) -> None:
        """Integrate wheel velocities to update odometry pose."""
        if dt <= 0.0:
            return

        # Compute base velocity from wheel velocities (forward kinematics)
        vx, vy, omega = self._compute_base_velocity(self._actual_wheel_velocities)

        # Store velocities
        self._odom_vx = vx
        self._odom_vy = vy
        self._odom_omega = omega

        # Transform velocity from robot frame to world frame
        cos_theta = math.cos(self._odom_theta)
        sin_theta = math.sin(self._odom_theta)

        vx_world = cos_theta * vx - sin_theta * vy
        vy_world = sin_theta * vx + cos_theta * vy

        # Integrate to update pose
        self._odom_x += vx_world * dt
        self._odom_y += vy_world * dt
        self._odom_theta += omega * dt

        # Normalize theta to [-pi, pi]
        self._odom_theta = math.atan2(math.sin(self._odom_theta), math.cos(self._odom_theta))

    def _publish_odometry(self, timestamp) -> None:
        """Publish odometry message and TF transform."""
        # Create quaternion from yaw
        qz = math.sin(self._odom_theta / 2.0)
        qw = math.cos(self._odom_theta / 2.0)

        # Publish TF transform (odom → base_link)
        t = TransformStamped()
        t.header.stamp = timestamp
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_plate_layer1_v5'  # Base link from URDF
        t.transform.translation.x = self._odom_x
        t.transform.translation.y = self._odom_y
        t.transform.translation.z = 0.0
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = qz
        t.transform.rotation.w = qw
        self._tf_broadcaster.sendTransform(t)

        # Publish odometry message
        odom = Odometry()
        odom.header.stamp = timestamp
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_plate_layer1_v5'

        # Pose
        odom.pose.pose.position.x = self._odom_x
        odom.pose.pose.position.y = self._odom_y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation.x = 0.0
        odom.pose.pose.orientation.y = 0.0
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw

        # Pose covariance (diagonal: x, y, z, roll, pitch, yaw)
        odom.pose.covariance = [
            0.01, 0.0,  0.0, 0.0, 0.0, 0.0,  # x
            0.0,  0.01, 0.0, 0.0, 0.0, 0.0,  # y
            0.0,  0.0,  1e6, 0.0, 0.0, 0.0,  # z (large - not measured)
            0.0,  0.0,  0.0, 1e6, 0.0, 0.0,  # roll (large - not measured)
            0.0,  0.0,  0.0, 0.0, 1e6, 0.0,  # pitch (large - not measured)
            0.0,  0.0,  0.0, 0.0, 0.0, 0.02  # yaw
        ]

        # Twist (velocity in robot frame)
        odom.twist.twist.linear.x = self._odom_vx
        odom.twist.twist.linear.y = self._odom_vy
        odom.twist.twist.linear.z = 0.0
        odom.twist.twist.angular.x = 0.0
        odom.twist.twist.angular.y = 0.0
        odom.twist.twist.angular.z = self._odom_omega

        # Twist covariance
        odom.twist.covariance = [
            0.01, 0.0,  0.0, 0.0, 0.0, 0.0,  # vx
            0.0,  0.01, 0.0, 0.0, 0.0, 0.0,  # vy
            0.0,  0.0,  1e6, 0.0, 0.0, 0.0,  # vz (large - not measured)
            0.0,  0.0,  0.0, 1e6, 0.0, 0.0,  # wx (large - not measured)
            0.0,  0.0,  0.0, 0.0, 1e6, 0.0,  # wy (large - not measured)
            0.0,  0.0,  0.0, 0.0, 0.0, 0.02  # wz
        ]

        self._odom_pub.publish(odom)


def main() -> None:
    rclpy.init()
    node = KiwiBaseController()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
