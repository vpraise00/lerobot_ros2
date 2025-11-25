"""
TF Utilities for LeKiwi Robot

Provides common TF operations and helpers.
"""

from __future__ import annotations

import math
from typing import Optional, Tuple

import rclpy
from geometry_msgs.msg import Quaternion, Transform, TransformStamped, Vector3
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener


class TFHelper:
    """Helper class for common TF operations."""

    def __init__(self, node: Node, buffer_size: int = 100):
        """
        Initialize TF helper.

        Args:
            node: ROS2 node instance.
            buffer_size: Size of TF buffer.
        """
        self.node = node
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, node)

    def lookup_transform(
        self,
        target_frame: str,
        source_frame: str,
        time: Optional[Time] = None,
        timeout_sec: float = 0.1,
    ) -> Optional[TransformStamped]:
        """
        Lookup transform between frames.

        Args:
            target_frame: Target frame ID.
            source_frame: Source frame ID.
            time: Time for transform lookup. If None, uses latest.
            timeout_sec: Timeout for transform lookup.

        Returns:
            TransformStamped if found, None otherwise.
        """
        if time is None:
            time = Time()

        try:
            timeout_duration = rclpy.duration.Duration(seconds=timeout_sec)
            transform = self.tf_buffer.lookup_transform(
                target_frame, source_frame, time, timeout=timeout_duration
            )
            return transform
        except Exception as e:
            self.node.get_logger().debug(
                f"Failed to lookup transform {source_frame} -> {target_frame}: {e}"
            )
            return None

    def check_frame_exists(self, frame_id: str, timeout_sec: float = 0.1) -> bool:
        """
        Check if frame exists in TF tree.

        Args:
            frame_id: Frame ID to check.
            timeout_sec: Timeout for check.

        Returns:
            True if frame exists, False otherwise.
        """
        try:
            timeout_duration = rclpy.duration.Duration(seconds=timeout_sec)
            # Try to get all frame names
            all_frames = self.tf_buffer.all_frames_as_string()
            return frame_id in all_frames
        except Exception:
            return False

    @staticmethod
    def create_transform_stamped(
        parent_frame: str,
        child_frame: str,
        translation: Tuple[float, float, float],
        rotation: Tuple[float, float, float, float],
        stamp: Optional[Time] = None,
    ) -> TransformStamped:
        """
        Create TransformStamped message.

        Args:
            parent_frame: Parent frame ID.
            child_frame: Child frame ID.
            translation: Translation as (x, y, z).
            rotation: Rotation as quaternion (x, y, z, w).
            stamp: Timestamp. If None, uses current time.

        Returns:
            TransformStamped message.
        """
        t = TransformStamped()

        if stamp is None:
            t.header.stamp = Time().to_msg()
        else:
            t.header.stamp = stamp.to_msg()

        t.header.frame_id = parent_frame
        t.child_frame_id = child_frame

        t.transform.translation.x = translation[0]
        t.transform.translation.y = translation[1]
        t.transform.translation.z = translation[2]

        t.transform.rotation.x = rotation[0]
        t.transform.rotation.y = rotation[1]
        t.transform.rotation.z = rotation[2]
        t.transform.rotation.w = rotation[3]

        return t

    @staticmethod
    def euler_to_quaternion(roll: float, pitch: float, yaw: float) -> Tuple[float, float, float, float]:
        """
        Convert Euler angles to quaternion.

        Args:
            roll: Roll angle in radians.
            pitch: Pitch angle in radians.
            yaw: Yaw angle in radians.

        Returns:
            Quaternion as (x, y, z, w).
        """
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)

        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy

        return (x, y, z, w)

    @staticmethod
    def quaternion_to_euler(q: Quaternion) -> Tuple[float, float, float]:
        """
        Convert quaternion to Euler angles.

        Args:
            q: Quaternion message.

        Returns:
            Euler angles as (roll, pitch, yaw) in radians.
        """
        # Roll (x-axis rotation)
        sinr_cosp = 2 * (q.w * q.x + q.y * q.z)
        cosr_cosp = 1 - 2 * (q.x * q.x + q.y * q.y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        # Pitch (y-axis rotation)
        sinp = 2 * (q.w * q.y - q.z * q.x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)  # Use 90 degrees if out of range
        else:
            pitch = math.asin(sinp)

        # Yaw (z-axis rotation)
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        return (roll, pitch, yaw)

    @staticmethod
    def normalize_angle(angle: float) -> float:
        """
        Normalize angle to [-pi, pi].

        Args:
            angle: Angle in radians.

        Returns:
            Normalized angle.
        """
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle
