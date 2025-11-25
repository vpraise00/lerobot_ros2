from __future__ import annotations

"""
Minimal MoveIt bringup for LeKiwi URDF (planning/visualization only).

This does not modify existing lerobot_ros2 behavior; it runs standalone
to provide move_group + robot_state_publisher with LeKiwi model.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List

import yaml
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def load_joint_names(config_path: Path) -> List[str]:
    data = yaml.safe_load(config_path.read_text()) or {}
    joints = data.get("joint_names", [])
    if not joints or not isinstance(joints, list):
        raise ValueError(f"'joint_names' missing in {config_path}")
    return [str(j) for j in joints]


def find_parent_child(urdf_path: Path, joint_name: str) -> tuple[str, str]:
    root = ET.parse(urdf_path).getroot()
    for j in root.findall("joint"):
        if j.get("name") == joint_name:
            parent = j.find("parent").get("link")
            child = j.find("child").get("link")
            return parent, child
    raise ValueError(f"Joint {joint_name} not found in {urdf_path}")


def build_srdf(robot_name: str, base_link: str, tip_link: str, joints: List[str]) -> str:
    joint_tags = "\n    ".join(f'<joint name="{j}"/>' for j in joints)
    return f"""<?xml version="1.0"?>
<robot name="{robot_name}">
  <virtual_joint name="world_joint" type="fixed" parent_frame="world" child_link="{base_link}"/>
  <group name="arm">
    {joint_tags}
  </group>
  <end_effector name="ee" parent_link="{tip_link}" group="arm"/>
</robot>
"""


def launch_setup(context, *args, **kwargs):
    ws_root = Path(__file__).resolve().parent.parent
    config_path = Path(LaunchConfiguration("config").perform(context))
    urdf_path = Path(LaunchConfiguration("urdf").perform(context))

    joint_names = load_joint_names(config_path)
    base_link, _ = find_parent_child(urdf_path, joint_names[0])
    _, tip_link = find_parent_child(urdf_path, joint_names[-1])
    srdf = build_srdf("lekiwi", base_link, tip_link, joint_names)

    robot_description = {"robot_description": urdf_path.read_text()}
    robot_description_semantic = {"robot_description_semantic": srdf}

    kinematics_yaml = {
        "robot_description_kinematics": {
            "arm": {
                "kinematics_solver": "kdl_kinematics_plugin/KDLKinematicsPlugin",
                "kinematics_solver_search_resolution": 0.005,
                "kinematics_solver_timeout": 0.1,
                "kinematics_solver_attempts": 3,
            }
        }
    }

    controllers_yaml = {
        "moveit_simple_controller_manager": {
            "controller_names": ["arm_controller"],
            "arm_controller": {
                "type": "FollowJointTrajectory",
                "joints": joint_names,
            },
        },
        "moveit_controller_manager": "moveit_simple_controller_manager/MoveItSimpleControllerManager",
    }

    planning_yaml = {
        "planning_pipelines": ["ompl"],
        "planning_plugin": "ompl_interface/OMPLPlanner",
        "request_adapters": "default_planning_request_adapters/AddTimeParameterization "
        "default_planning_request_adapters/FixWorkspaceBounds "
        "default_planning_request_adapters/FixStartStateBounds "
        "default_planning_request_adapters/FixStartStateCollision "
        "default_planning_request_adapters/FixStartStatePathConstraints",
        "start_state_max_bounds_error": 0.1,
    }

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description],
    )

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            controllers_yaml,
            planning_yaml,
        ],
    )

    return [robot_state_publisher_node, move_group_node]


def generate_launch_description() -> LaunchDescription:
    ws_root = Path(__file__).resolve().parent.parent.parent  # scripts/lekiwi -> lerobot_ros2
    default_config = ws_root / "src" / "lekiwi_isaac_bridge" / "config" / "lekiwi_sim.yaml"
    default_urdf = ws_root / "urdf" / "lekiwi" / "lekiwi.urdf"

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "config",
                default_value=str(default_config),
                description="Path to lekiwi_sim.yaml with joint_names",
            ),
            DeclareLaunchArgument(
                "urdf",
                default_value=str(default_urdf),
                description="Path to lekiwi URDF",
            ),
            OpaqueFunction(function=launch_setup),
        ]
    )
