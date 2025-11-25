"""
Core launch file for LeKiwi robot.

Launches essential nodes required for all scenarios:
- robot_state_publisher: Publishes TF tree from URDF
- static_transform_publisher: Links base_link to base_plate_layer1_v5
- hardware_interface: Bridges Isaac Sim joint_states ↔ joint_command
- command_arbiter: Priority-based command arbitration
"""

from __future__ import annotations

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def load_repo_urdf() -> str:
    share_dir = Path(get_package_share_directory("lekiwi_description"))
    urdf_path = share_dir / "urdf" / "lekiwi.urdf"
    if not urdf_path.exists():
        raise FileNotFoundError(f"LeKiwi URDF not found at: {urdf_path}")
    return urdf_path.read_text()


def generate_launch_description() -> LaunchDescription:
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    robot_description = load_repo_urdf()
    robot_description_param = {"robot_description": robot_description}

    # Robot state publisher - publishes TF tree from URDF
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="lekiwi_state_publisher",
        output="screen",
        parameters=[
            {"use_sim_time": use_sim_time},
            robot_description_param,
            {
                "qos_overrides./joint_states.subscription.reliability": "reliable",
                "qos_overrides./joint_states.subscription.history": "keep_last",
                "qos_overrides./joint_states.subscription.depth": 10,
            },
        ],
    )

    # Static TF: base_link → base_plate_layer1_v5
    static_tf_publisher = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0", "0", "0", "0", "base_link", "base_plate_layer1_v5"],
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
    )

    # Hardware interface - aggregates base/arm commands → /joint_command
    hardware_interface = Node(
        package="lekiwi_hardware",
        executable="hardware_interface",
        name="lekiwi_hardware_interface",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
    )

    # Command arbiter - priority-based command selection
    command_arbiter = Node(
        package="lekiwi_command_arbiter",
        executable="command_arbiter",
        name="lekiwi_command_arbiter",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            SetEnvironmentVariable(name="RCUTILS_COLORIZED_OUTPUT", value="1"),
            robot_state_publisher,
            static_tf_publisher,
            hardware_interface,
            command_arbiter,
        ]
    )
