from __future__ import annotations

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    share = Path(get_package_share_directory("lekiwi_trajectory_bridge"))
    config_file = LaunchConfiguration("config_file")
    use_sim_time = LaunchConfiguration("use_sim_time")

    executor = Node(
        package="lekiwi_trajectory_bridge",
        executable="lekiwi_arm_trajectory_executor",
        output="screen",
        parameters=[config_file, {"use_sim_time": use_sim_time}],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("config_file", default_value=str(share / "config" / "trajectory_bridge.yaml")),
            executor,
        ]
    )
