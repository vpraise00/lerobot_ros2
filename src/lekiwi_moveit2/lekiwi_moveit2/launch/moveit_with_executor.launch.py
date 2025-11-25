from __future__ import annotations

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description() -> LaunchDescription:
    use_sim_time = LaunchConfiguration("use_sim_time")
    start_executor = LaunchConfiguration("start_executor")
    launch_rviz = LaunchConfiguration("launch_rviz")

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

    rviz_config = Path(get_package_share_directory("lekiwi_moveit2")) / "config" / "moveit.rviz"

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            {
                **moveit_config.to_dict(),
                "planning_scene_monitor": {
                    "publish_planning_scene": True,
                    "publish_planning_scene_frequency": 1.0,  # ensure periodic scene publishing
                    "publish_geometry_updates": False,  # 환경 지오메트리 업데이트 끔 (씬 메시지 축소)
                    "publish_state_updates": True,
                    "publish_transform_updates": True,
                    "provide_planning_scene_service": True,
                },
                "use_sim_time": use_sim_time,
            }
        ],
    )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        # Pass the prebuilt robot_description dict directly; wrapping it again leaves the parameter empty
        parameters=[moveit_config.robot_description, {"use_sim_time": use_sim_time}],
    )

    rviz_node_delayed = TimerAction(
        period=3.0,
        actions=[
            Node(
                package="rviz2",
                executable="rviz2",
                name="lekiwi_moveit_rviz",
                output="screen",
                arguments=["-d", str(rviz_config)],
                parameters=[
                    {
                        **moveit_config.to_dict(),
                "planning_scene_monitor": {
                    "publish_planning_scene": True,
                    "publish_planning_scene_frequency": 1.0,
                    "publish_geometry_updates": False,  # 환경 지오메트리 업데이트 끔 (씬 메시지 축소)
                    "publish_state_updates": True,
                    "publish_transform_updates": True,
                    "provide_planning_scene_service": True,
                },
                        "use_sim_time": use_sim_time,
                    }
                ],
                condition=IfCondition(launch_rviz),
            )
        ],
    )

    executor_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(Path(get_package_share_directory("lekiwi_trajectory_bridge")) / "launch" / "trajectory_executor.launch.py")
        ),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
        condition=IfCondition(start_executor),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("start_executor", default_value="true"),
            DeclareLaunchArgument(
                "launch_rviz",
                default_value="true",
                description="Set false to skip RViz2 (run a separate RViz with custom QoS settings).",
            ),
            robot_state_publisher_node,
            move_group_node,
            rviz_node_delayed,
            executor_launch,
        ]
    )
