from __future__ import annotations

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.conditions import IfCondition
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
    start_bridge = LaunchConfiguration("start_bridge", default="true")

    robot_description = load_repo_urdf()
    robot_description_param = {"robot_description": robot_description}

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

    bridge_node = Node(
        package="lekiwi_isaac_bridge",
        executable="bridge_node",
        name="lekiwi_joint_bridge",
        condition=IfCondition(start_bridge),
        output="screen",
        parameters=[
            {
                "config": str(
                    Path(get_package_share_directory("lekiwi_isaac_bridge")) / "config" / "lekiwi_sim.yaml"
                )
            }
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("start_bridge", default_value="true"),
            SetEnvironmentVariable(name="RCUTILS_COLORIZED_OUTPUT", value="1"),
            robot_state_publisher,
            Node(
                package="tf2_ros",
                executable="static_transform_publisher",
                arguments=["0", "0", "0", "0", "0", "0", "base_link", "base_plate_layer1_v5"],
                output="screen",
            ),
            bridge_node,
        ]
    )
