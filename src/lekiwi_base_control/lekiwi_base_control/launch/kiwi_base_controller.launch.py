from __future__ import annotations

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    share = Path(get_package_share_directory("lekiwi_base_control"))
    config_file = LaunchConfiguration("controller_config")
    use_sim_time = LaunchConfiguration("use_sim_time")

    controller = Node(
        package="lekiwi_base_control",
        executable="lekiwi_kiwi_base_controller",
        output="screen",
        parameters=[config_file, {"use_sim_time": use_sim_time}],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("controller_config", default_value=str(share / "config" / "kiwi_base_controller.yaml")),
            controller,
        ]
    )
