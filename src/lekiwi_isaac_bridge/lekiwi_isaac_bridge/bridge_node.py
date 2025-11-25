from __future__ import annotations

import pathlib
from typing import List

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray
import yaml

try:
    from ament_index_python.packages import get_package_share_directory
except ImportError:  # pragma: no cover
    get_package_share_directory = None  # type: ignore


DEFAULT_PACKAGE = "lekiwi_isaac_bridge"
DEFAULT_INPUT_TOPIC = "/joint_commands"
DEFAULT_OUTPUT_TOPIC = "/joint_command"


class LeKiwiIsaacBridge(Node):
    """Sidecar bridge: Float64MultiArray → JointState for Isaac Sim LeKiwi.

    - Subscribes to input_topic (Float64MultiArray)
    - Publishes to output_topic (JointState) with configured joint_names order
    """

    def __init__(self) -> None:
        super().__init__("lekiwi_isaac_bridge")

        # Parameters
        default_config_path = self._default_config_path()
        self.declare_parameter("config", str(default_config_path))
        self.declare_parameter("input_topic", DEFAULT_INPUT_TOPIC)
        self.declare_parameter("output_topic", DEFAULT_OUTPUT_TOPIC)

        config_path = pathlib.Path(self.get_parameter("config").get_parameter_value().string_value)
        input_topic = self.get_parameter("input_topic").get_parameter_value().string_value
        output_topic = self.get_parameter("output_topic").get_parameter_value().string_value

        # Load joint names
        self.joint_names = self._load_joint_names(config_path)
        self.expected_len = len(self.joint_names)
        self._last_mismatch_size: int | None = None

        qos = QoSProfile(depth=10)
        self.pub = self.create_publisher(JointState, output_topic, qos)
        self.sub = self.create_subscription(Float64MultiArray, input_topic, self._on_command, qos)

        self.get_logger().info(
            "LeKiwi Isaac bridge ready"
            f"\n  config: {config_path}"
            f"\n  input_topic: {input_topic}"
            f"\n  output_topic: {output_topic}"
            f"\n  joints ({self.expected_len}): {self.joint_names}"
        )

    def _default_config_path(self) -> pathlib.Path:
        """Return default config path inside the package share directory."""
        if get_package_share_directory is None:
            return pathlib.Path("config/lekiwi_sim.yaml")
        try:
            share_dir = pathlib.Path(get_package_share_directory(DEFAULT_PACKAGE))
            return share_dir / "config" / "lekiwi_sim.yaml"
        except Exception:
            return pathlib.Path("config/lekiwi_sim.yaml")

    def _load_joint_names(self, path: pathlib.Path) -> List[str]:
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        joint_names = data.get("joint_names")
        if not joint_names or not isinstance(joint_names, list):
            raise ValueError(f"Config missing 'joint_names' list: {path}")

        # Normalize to strings
        return [str(name) for name in joint_names]

    def _on_command(self, msg: Float64MultiArray) -> None:
        data = list(msg.data)
        if len(data) != self.expected_len:
            if self._last_mismatch_size != len(data):
                self.get_logger().warning(
                    f"Drop command: expected {self.expected_len} joints, got {len(data)}"
                )
                self._last_mismatch_size = len(data)
            return

        self._last_mismatch_size = None

        out = JointState()
        out.header.stamp = self.get_clock().now().to_msg()
        out.name = self.joint_names
        out.position = data
        # velocity/effort left empty; can be extended to zeros if needed

        self.pub.publish(out)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = LeKiwiIsaacBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":  # pragma: no cover
    main()
