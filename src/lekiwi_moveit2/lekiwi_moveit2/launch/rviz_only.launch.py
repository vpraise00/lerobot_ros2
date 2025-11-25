from __future__ import annotations

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description() -> LaunchDescription:
    use_sim_time = LaunchConfiguration("use_sim_time")

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

    rviz_node = Node(
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
                    "publish_geometry_updates": False,
                    "publish_state_updates": True,
                    "publish_transform_updates": True,
                    "provide_planning_scene_service": True,
                },
                "use_sim_time": use_sim_time,
            }
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            rviz_node,
        ]
    )
