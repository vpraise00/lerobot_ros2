from __future__ import annotations

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")
    params_file = LaunchConfiguration("params_file")

    share_dir = Path(get_package_share_directory("lekiwi_nav2"))
    default_params = share_dir / "config" / "nav2_params.yaml"
    slam_params = share_dir / "config" / "slam_params.yaml"

    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(Path(get_package_share_directory("nav2_bringup")) / "launch" / "navigation_launch.py")
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "params_file": params_file,
        }.items(),
    )

    slam = Node(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="lekiwi_slam",
        output="screen",
        parameters=[slam_params, {"use_sim_time": use_sim_time}],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("params_file", default_value=str(default_params)),
            slam,
            nav2_launch,
        ]
    )
