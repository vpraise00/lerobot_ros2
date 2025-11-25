"""
MoveIt2 launch file for LeKiwi robot.

Launches core nodes + arm motion planning:
- Core nodes (via lekiwi_core.launch.py)
- MoveIt2 move_group: Arm motion planning and execution

Usage:
    ros2 launch lekiwi_bringup lekiwi_moveit2.launch.py

Note:
    Requires MoveIt2 configuration in lekiwi_moveit2 package.
    If config not found, will launch core nodes only.
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

    # TODO: Add MoveIt2 launch when configuration is ready
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

    # Placeholder: MoveIt2 command publisher for arm control
    # This allows testing arm commands even without full MoveIt2 setup
    arm_teleop_placeholder = Node(
        package="lekiwi_command_arbiter",
        executable="command_arbiter",
        name="arm_command_placeholder",
        output="screen",
        parameters=[
            {"use_sim_time": use_sim_time},
        ],
        remappings=[
            # Remap for future MoveIt2 integration
            # ("/move_group/display_planned_path", "/arm_command_manipulation"),
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            core_launch,
            # moveit2_launch,  # Uncomment when MoveIt2 config is ready
        ]
    )
