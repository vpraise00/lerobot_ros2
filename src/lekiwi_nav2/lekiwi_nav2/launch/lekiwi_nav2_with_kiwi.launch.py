from __future__ import annotations

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    share_dir = Path(get_package_share_directory("lekiwi_nav2"))
    use_sim_time = LaunchConfiguration("use_sim_time")
    params_file = LaunchConfiguration("params_file")
    controller_config = LaunchConfiguration("controller_config")
    start_controller = LaunchConfiguration("start_controller")

    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(Path(get_package_share_directory("nav2_bringup")) / "launch" / "navigation_launch.py")
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "params_file": params_file,
        }.items(),
    )

    slam_params = share_dir / "config" / "slam_params.yaml"
    slam = Node(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="lekiwi_slam",
        output="screen",
        parameters=[slam_params, {"use_sim_time": use_sim_time}],
    )

    base_controller = Node(
        package="lekiwi_base_control",
        executable="lekiwi_kiwi_base_controller",
        name="lekiwi_kiwi_base_controller",
        output="screen",
        parameters=[controller_config, {"use_sim_time": use_sim_time}],
        condition=IfCondition(start_controller),
    )

    # Default Nav2 RViz config from nav2_bringup
    nav2_rviz_config = (
        Path(get_package_share_directory("nav2_bringup")) / "rviz" / "nav2_default_view.rviz"
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="lekiwi_nav2_rviz",
        output="screen",
        arguments=["-d", str(nav2_rviz_config)],
        parameters=[{"use_sim_time": use_sim_time}],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("params_file", default_value=str(share_dir / "config" / "nav2_params.yaml")),
            DeclareLaunchArgument(
                "controller_config",
                default_value=str(Path(get_package_share_directory("lekiwi_base_control")) / "config" / "kiwi_base_controller.yaml"),
            ),
            DeclareLaunchArgument("start_controller", default_value="true"),
            slam,
            base_controller,
            nav2_launch,
            rviz_node,
        ]
    )
