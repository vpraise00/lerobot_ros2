"""
Mobile manipulation launch file for LeKiwi robot.

Launches complete system with simultaneous base + arm control:
- Core nodes (via lekiwi_core.launch.py)
- base_controller: Publishes odometry for Nav2
- Nav2 stack: Autonomous navigation
- MoveIt2 move_group: Arm motion planning

Command Priority (handled by command_arbiter):
    Emergency Stop (255) > Teleop (200) > Manipulation (150) > Navigation (100)

Usage:
    ros2 launch lekiwi_bringup lekiwi_mobile_manip.launch.py

Examples:
    # Nav2 moves base while MoveIt2 controls arm (no conflict)
    ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose ...
    ros2 action send_goal /move_group moveit_msgs/action/MoveGroup ...

    # Teleop overrides both Nav2 and MoveIt2
    ros2 topic pub /cmd_vel_teleop geometry_msgs/Twist "{linear: {x: 0.1}}" --once
"""

from __future__ import annotations

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    # Nav2 configuration
    nav2_config_path = PathJoinSubstitution([
        FindPackageShare("lekiwi_nav2"),
        "config",
        "kiwi_drive_controller.yaml"
    ])

    # Include core launch file
    core_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("lekiwi_bringup"),
                "launch",
                "lekiwi_core.launch.py"
            ])
        ]),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
    )

    # Base controller - publishes odometry for Nav2
    base_controller = Node(
        package="lekiwi_base_control",
        executable="base_controller_node",
        name="lekiwi_base_controller",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
    )

    # Nav2 bringup
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("nav2_bringup"),
                "launch",
                "navigation_launch.py"
            ])
        ]),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "params_file": nav2_config_path,
        }.items(),
    )

    # TODO: MoveIt2 launch when configuration is ready
    # moveit2_launch = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource([
    #         PathJoinSubstitution([
    #             FindPackageShare("lekiwi_moveit2"),
    #             "launch",
    #             "move_group.launch.py"
    #         ])
    #     ]),
    #     launch_arguments={
    #         "use_sim_time": use_sim_time,
    #     }.items(),
    # )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            core_launch,
            base_controller,
            nav2_launch,
            # moveit2_launch,  # Uncomment when MoveIt2 config is ready
        ]
    )
