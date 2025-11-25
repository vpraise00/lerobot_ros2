from __future__ import annotations

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    share_dir = Path(get_package_share_directory("lekiwi_perception"))

    use_sim_time = LaunchConfiguration("use_sim_time")
    config_file = LaunchConfiguration("config_file")
    raw_topic = LaunchConfiguration("perception_image_topic")
    raw_info = LaunchConfiguration("perception_info_topic")
    rect_topic = LaunchConfiguration("rectified_image_topic")
    debayer_topic = LaunchConfiguration("debayered_image_topic")

    bridge_node = Node(
        package="lekiwi_perception",
        executable="camera_bridge_node",
        name="lekiwi_camera_bridge",
        output="screen",
        parameters=[config_file, {"use_sim_time": use_sim_time}],
    )

    debayer_node = Node(
        package="image_proc",
        executable="debayer_node",
        name="lekiwi_debayer_node",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
        remappings=[
            ("image_raw", raw_topic),
            ("image", debayer_topic),
        ],
    )

    rectify_node = Node(
        package="image_proc",
        executable="rectify_node",
        name="lekiwi_rectify_node",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
        remappings=[
            ("image", debayer_topic),
            ("camera_info", raw_info),
            ("image_rect", rect_topic),
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("config_file", default_value=str(share_dir / "config" / "camera_bridge.yaml")),
            DeclareLaunchArgument("perception_image_topic", default_value="/lekiwi/perception/front/image_raw"),
            DeclareLaunchArgument("perception_info_topic", default_value="/lekiwi/perception/front/camera_info"),
            DeclareLaunchArgument("rectified_image_topic", default_value="/lekiwi/perception/front/image_rect"),
            DeclareLaunchArgument("debayered_image_topic", default_value="/lekiwi/perception/front/image_color"),
            bridge_node,
            debayer_node,
            rectify_node,
        ]
    )
