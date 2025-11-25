from __future__ import annotations

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from pathlib import Path

from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description() -> LaunchDescription:
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    moveit_config = (
        MoveItConfigsBuilder("lekiwi", package_name="lekiwi_description")
        .robot_description(file_path="urdf/lekiwi.urdf")
        .robot_description_semantic(file_path="srdf/lekiwi.srdf")
        .robot_description_kinematics(file_path="config/kinematics.yaml")
        .joint_limits(file_path="config/joint_limits.yaml")
        .trajectory_execution(file_path="config/trajectory_execution.yaml")
        .pilz_cartesian_limits(file_path="config/pilz_cartesian_limits.yaml")
        .planning_scene_monitor(
            publish_robot_description=True,
            publish_robot_description_semantic=True,
        )
        .to_moveit_configs()
    )
    moveit_config.planning_scene_monitor["provide_planning_scene_service"] = True

    rviz_config = Path(get_package_share_directory("lekiwi_moveit2")) / "config" / "moveit.rviz"

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": moveit_config.robot_description, "use_sim_time": use_sim_time}],
    )

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            {"use_sim_time": use_sim_time},
        ],
    )

    # Delay RViz startup slightly so MoveGroup has time to advertise the
    # planning scene service before the MotionPlanning panel requests it.
    rviz_node = TimerAction(
        period=3.0,
        actions=[Node(
        package="rviz2",
        executable="rviz2",
        name="lekiwi_moveit_rviz",
        output="screen",
        arguments=["-d", str(rviz_config)],
        parameters=[{**moveit_config.to_dict(), "use_sim_time": use_sim_time}],
    )],
    )

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        robot_state_publisher_node,
        move_group_node,
        rviz_node,
    ])
