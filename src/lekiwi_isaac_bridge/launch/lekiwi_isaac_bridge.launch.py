from __future__ import annotations

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    package_share = Path(get_package_share_directory("lekiwi_isaac_bridge"))
    default_config = package_share / "config" / "lekiwi_sim.yaml"

    config_arg = DeclareLaunchArgument(
        "config",
        default_value=str(default_config),
        description="Path to YAML with joint_names/input/output topics",
    )

    input_arg = DeclareLaunchArgument(
        "input_topic",
        default_value="/joint_commands",
        description="Input Float64MultiArray topic",
    )

    output_arg = DeclareLaunchArgument(
        "output_topic",
        default_value="/joint_command",
        description="Output JointState topic",
    )

    bridge_node = Node(
        package="lekiwi_isaac_bridge",
        executable="bridge_node",
        name="lekiwi_isaac_bridge",
        output="screen",
        parameters=[
            {
                "config": LaunchConfiguration("config"),
                "input_topic": LaunchConfiguration("input_topic"),
                "output_topic": LaunchConfiguration("output_topic"),
            }
        ],
    )

    return LaunchDescription([config_arg, input_arg, output_arg, bridge_node])
