from __future__ import annotations

import message_filters
import rclpy
from builtin_interfaces.msg import Time
from rclpy.node import Node
from rclpy.qos import QoSPresetProfiles
from sensor_msgs.msg import CameraInfo, Image


class CameraBridgeNode(Node):
    """Simple QoS-aware relay for the Isaac Sim camera topics."""

    def __init__(self) -> None:
        super().__init__("lekiwi_camera_bridge")

        self.declare_parameter("input_image_topic", "/lekiwi/camera/front/image_raw")
        self.declare_parameter("input_info_topic", "/lekiwi/camera/front/camera_info")
        self.declare_parameter("output_image_topic", "/lekiwi/perception/front/image_raw")
        self.declare_parameter("output_info_topic", "/lekiwi/perception/front/camera_info")
        self.declare_parameter("camera_frame_id", "lekiwi_camera_front_optical_frame")
        self.declare_parameter("queue_size", 10)
        self.declare_parameter("approx_sync_tolerance", 0.05)

        input_image_topic: str = self.get_parameter("input_image_topic").get_parameter_value().string_value
        input_info_topic: str = self.get_parameter("input_info_topic").get_parameter_value().string_value
        self._output_image_topic: str = (
            self.get_parameter("output_image_topic").get_parameter_value().string_value
        )
        self._output_info_topic: str = (
            self.get_parameter("output_info_topic").get_parameter_value().string_value
        )
        self._frame_id: str = self.get_parameter("camera_frame_id").get_parameter_value().string_value
        queue_size = self.get_parameter("queue_size").get_parameter_value().integer_value
        approx_sync_tol = self.get_parameter("approx_sync_tolerance").get_parameter_value().double_value

        qos = QoSPresetProfiles.SENSOR_DATA.value

        self._image_pub = self.create_publisher(Image, self._output_image_topic, qos)
        self._info_pub = self.create_publisher(CameraInfo, self._output_info_topic, qos)

        self._image_sub = message_filters.Subscriber(self, Image, input_image_topic, qos_profile=qos)
        self._info_sub = message_filters.Subscriber(self, CameraInfo, input_info_topic, qos_profile=qos)

        self._sync = message_filters.ApproximateTimeSynchronizer(
            [self._image_sub, self._info_sub],
            queue_size=max(queue_size, 2),
            slop=max(approx_sync_tol, 0.005),
        )
        self._sync.registerCallback(self._synced_callback)

        self.get_logger().info(
            "LeKiwi camera bridge ready\n"
            f"  input image:  {input_image_topic}\n"
            f"  input info:   {input_info_topic}\n"
            f"  output image: {self._output_image_topic}\n"
            f"  output info:  {self._output_info_topic}"
        )

    def _synced_callback(self, image: Image, info: CameraInfo) -> None:
        """Publish camera data to Nav2 / VSLAM friendly topics."""
        now = self.get_clock().now().to_msg()
        image.header = _with_frame(image.header, self._frame_id, now)
        info.header = _with_frame(info.header, self._frame_id, now)
        self._image_pub.publish(image)
        self._info_pub.publish(info)


def _with_frame(header, frame_id: str, stamp: Time):
    header.frame_id = frame_id
    header.stamp = stamp
    return header


def main() -> None:
    rclpy.init()
    node = CameraBridgeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
