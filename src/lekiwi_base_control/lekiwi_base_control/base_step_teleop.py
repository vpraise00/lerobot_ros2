from __future__ import annotations

import math
import select
import signal
import sys
import termios
import tty
from typing import Optional

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import QoSPresetProfiles


def _wrap_angle(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


class KeyPoseStepper(Node):
    """Keyboard-based pose stepper: increment target (x, y, yaw) and track it with cmd_vel."""

    def __init__(self) -> None:
        super().__init__("lekiwi_key_pose_stepper")

        # Parameters
        self.declare_parameter("odom_topic", "/odom")
        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("step_x", 0.05)  # meters per key press (forward/back)
        self.declare_parameter("step_y", 0.05)  # meters per key press (left/right)
        self.declare_parameter("step_yaw_deg", 5.0)  # degrees per key press
        self.declare_parameter("kp_lin", 1.5)
        self.declare_parameter("kp_ang", 2.0)
        self.declare_parameter("max_lin", 0.5)
        self.declare_parameter("max_ang", 1.0)
        self.declare_parameter("publish_rate_hz", 20.0)

        # Load parameters
        self._odom_topic = self.get_parameter("odom_topic").get_parameter_value().string_value
        self._cmd_vel_topic = self.get_parameter("cmd_vel_topic").get_parameter_value().string_value
        self._step_x = float(self.get_parameter("step_x").value)
        self._step_y = float(self.get_parameter("step_y").value)
        self._step_yaw = math.radians(float(self.get_parameter("step_yaw_deg").value))
        self._kp_lin = float(self.get_parameter("kp_lin").value)
        self._kp_ang = float(self.get_parameter("kp_ang").value)
        self._max_lin = float(self.get_parameter("max_lin").value)
        self._max_ang = float(self.get_parameter("max_ang").value)
        rate_hz = float(self.get_parameter("publish_rate_hz").value)
        self._period = 1.0 / max(rate_hz, 1.0)

        # State
        self._target_x = 0.0
        self._target_y = 0.0
        self._target_yaw = 0.0
        self._pose: Optional[tuple[float, float, float]] = None  # x, y, yaw
        self._has_init_target = False

        # ROS interfaces
        qos = QoSPresetProfiles.SENSOR_DATA.value
        self._odom_sub = self.create_subscription(Odometry, self._odom_topic, self._on_odom, qos)
        self._cmd_pub = self.create_publisher(Twist, self._cmd_vel_topic, qos)

        # Setup terminal for non-blocking key read
        self._stdin_fd = sys.stdin.fileno()
        self._stdin_attr = termios.tcgetattr(self._stdin_fd)
        tty.setcbreak(self._stdin_fd)
        signal.signal(signal.SIGINT, self._sigint_handler)

        self._timer = self.create_timer(self._period, self._on_timer)

        self.get_logger().info(
            "Key pose stepper ready (odom → cmd_vel)\n"
            f"  odom: {self._odom_topic}\n"
            f"  cmd_vel: {self._cmd_vel_topic}\n"
            f"  step: dx={self._step_x} m, dy={self._step_y} m, dyaw={math.degrees(self._step_yaw)} deg\n"
            f"  gains: kp_lin={self._kp_lin}, kp_ang={self._kp_ang}\n"
            f"  limits: max_lin={self._max_lin} m/s, max_ang={self._max_ang} rad/s"
        )
        self._print_help()

    def destroy_node(self) -> bool:
        try:
            termios.tcsetattr(self._stdin_fd, termios.TCSADRAIN, self._stdin_attr)
        except Exception:
            pass
        return super().destroy_node()

    def _sigint_handler(self, signum, frame) -> None:  # type: ignore[override]
        self.destroy_node()
        rclpy.shutdown()

    def _print_help(self) -> None:
        self.get_logger().info(
            "Keys: i/k forward/back, j/l left/right, u/o ccw/cw, space reset target, q exit"
        )

    def _on_odom(self, msg: Odometry) -> None:
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        self._pose = (x, y, yaw)
        if not self._has_init_target:
            self._target_x = x
            self._target_y = y
            self._target_yaw = yaw
            self._has_init_target = True

    def _read_key(self) -> Optional[str]:
        if not select.select([sys.stdin], [], [], 0)[0]:
            return None
        return sys.stdin.read(1)

    def _on_timer(self) -> None:
        key = self._read_key()
        if key:
            if key in ("q", "\x03"):
                self._sigint_handler(signal.SIGINT, None)
                return
            elif key == "i":
                self._target_x += self._step_x
            elif key == "k":
                self._target_x -= self._step_x
            elif key == "j":
                self._target_y += self._step_y
            elif key == "l":
                self._target_y -= self._step_y
            elif key == "u":
                self._target_yaw += self._step_yaw
            elif key == "o":
                self._target_yaw -= self._step_yaw
            elif key == " ":
                if self._pose is not None:
                    self._target_x, self._target_y, self._target_yaw = self._pose
                else:
                    self._target_x = 0.0
                    self._target_y = 0.0
                    self._target_yaw = 0.0
            elif key == "h":
                self._print_help()

        if self._pose is None:
            return

        x, y, yaw = self._pose
        # Position error in world frame
        ex = self._target_x - x
        ey = self._target_y - y
        e_yaw = _wrap_angle(self._target_yaw - yaw)

        # Transform position error into robot frame
        cos_yaw = math.cos(yaw)
        sin_yaw = math.sin(yaw)
        ex_b = cos_yaw * ex + sin_yaw * ey
        ey_b = -sin_yaw * ex + cos_yaw * ey

        vx = self._kp_lin * ex_b
        vy = self._kp_lin * ey_b
        wz = self._kp_ang * e_yaw

        # Clamp velocities
        vx = max(-self._max_lin, min(self._max_lin, vx))
        vy = max(-self._max_lin, min(self._max_lin, vy))
        wz = max(-self._max_ang, min(self._max_ang, wz))

        msg = Twist()
        msg.linear.x = vx
        msg.linear.y = vy
        msg.angular.z = wz
        self._cmd_pub.publish(msg)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = KeyPoseStepper()
    try:
        rclpy.spin(node)
    finally:
        if rclpy.ok():
            node.destroy_node()
        else:
            try:
                node.destroy_node()
            except Exception:
                pass


if __name__ == "__main__":
    main()
