"""
QoS Profile Management for LeKiwi Robot

Provides centralized QoS configuration loading and validation.
Ensures all nodes use compatible QoS settings, especially for Isaac Sim integration.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

import yaml
from ament_index_python.packages import get_package_share_directory
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    LivelinessPolicy,
    QoSProfile,
    ReliabilityPolicy,
)


class QoSManager:
    """Manages QoS profiles from centralized configuration."""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize QoS manager.

        Args:
            config_file: Path to QoS configuration YAML file.
                        If None, loads default from lekiwi_core package.
        """
        if config_file is None:
            pkg_share = get_package_share_directory("lekiwi_core")
            config_file = os.path.join(pkg_share, "config", "qos_profiles.yaml")

        self.config_file = Path(config_file)
        self.profiles: Dict[str, QoSProfile] = {}
        self._load_profiles()

    def _load_profiles(self) -> None:
        """Load QoS profiles from configuration file."""
        if not self.config_file.exists():
            raise FileNotFoundError(f"QoS config file not found: {self.config_file}")

        with open(self.config_file) as f:
            config = yaml.safe_load(f)

        qos_config = config.get("qos_profiles", {})

        for profile_name, profile_config in qos_config.items():
            self.profiles[profile_name] = self._create_qos_profile(profile_config)

        # Load default profile
        if "default" in config:
            self.profiles["default"] = self._create_qos_profile(config["default"])

    def _create_qos_profile(self, config: dict) -> QoSProfile:
        """
        Create QoSProfile from configuration dictionary.

        Args:
            config: Dictionary with QoS settings.

        Returns:
            Configured QoSProfile.
        """
        # Map string values to enum values
        reliability_map = {
            "reliable": ReliabilityPolicy.RELIABLE,
            "best_effort": ReliabilityPolicy.BEST_EFFORT,
        }

        durability_map = {
            "transient_local": DurabilityPolicy.TRANSIENT_LOCAL,
            "volatile": DurabilityPolicy.VOLATILE,
        }

        history_map = {
            "keep_last": HistoryPolicy.KEEP_LAST,
            "keep_all": HistoryPolicy.KEEP_ALL,
        }

        liveliness_map = {
            "automatic": LivelinessPolicy.AUTOMATIC,
            "manual_by_topic": LivelinessPolicy.MANUAL_BY_TOPIC,
        }

        # Create QoS profile
        profile = QoSProfile(
            reliability=reliability_map.get(
                config.get("reliability", "reliable"), ReliabilityPolicy.RELIABLE
            ),
            durability=durability_map.get(
                config.get("durability", "volatile"), DurabilityPolicy.VOLATILE
            ),
            history=history_map.get(config.get("history", "keep_last"), HistoryPolicy.KEEP_LAST),
            depth=config.get("depth", 10),
            liveliness=liveliness_map.get(
                config.get("liveliness", "automatic"), LivelinessPolicy.AUTOMATIC
            ),
        )

        # Set deadline if specified
        if "deadline" in config:
            deadline = config["deadline"]
            profile.deadline.sec = deadline.get("sec", 0)
            profile.deadline.nsec = deadline.get("nsec", 0)

        # Set lifespan if specified
        if "lifespan" in config:
            lifespan = config["lifespan"]
            profile.lifespan.sec = lifespan.get("sec", 0)
            profile.lifespan.nsec = lifespan.get("nsec", 0)

        # Set liveliness_lease_duration if specified
        if "liveliness_lease_duration" in config:
            lld = config["liveliness_lease_duration"]
            profile.liveliness_lease_duration.sec = lld.get("sec", 0)
            profile.liveliness_lease_duration.nsec = lld.get("nsec", 0)

        return profile

    def get(self, profile_name: str) -> QoSProfile:
        """
        Get QoS profile by name.

        Args:
            profile_name: Name of the profile (e.g., 'joint_states', 'camera_images').

        Returns:
            QoSProfile for the requested profile.

        Raises:
            KeyError: If profile name not found.
        """
        if profile_name not in self.profiles:
            if "default" in self.profiles:
                return self.profiles["default"]
            raise KeyError(f"QoS profile '{profile_name}' not found and no default profile available")

        return self.profiles[profile_name]

    def list_profiles(self) -> list[str]:
        """
        List all available profile names.

        Returns:
            List of profile names.
        """
        return list(self.profiles.keys())

    def validate_compatibility(
        self, publisher_profile: str, subscriber_profile: str
    ) -> tuple[bool, str]:
        """
        Validate if publisher and subscriber QoS profiles are compatible.

        Args:
            publisher_profile: Name of publisher's QoS profile.
            subscriber_profile: Name of subscriber's QoS profile.

        Returns:
            Tuple of (is_compatible, message).
        """
        try:
            pub_qos = self.get(publisher_profile)
            sub_qos = self.get(subscriber_profile)
        except KeyError as e:
            return False, str(e)

        # Check reliability compatibility
        # RELIABLE publisher can match RELIABLE or BEST_EFFORT subscriber
        # BEST_EFFORT publisher can only match BEST_EFFORT subscriber
        if (
            pub_qos.reliability == ReliabilityPolicy.BEST_EFFORT
            and sub_qos.reliability == ReliabilityPolicy.RELIABLE
        ):
            return (
                False,
                f"Incompatible reliability: publisher={pub_qos.reliability}, subscriber={sub_qos.reliability}",
            )

        # Check durability compatibility
        # TRANSIENT_LOCAL publisher can match any subscriber
        # VOLATILE publisher can only match VOLATILE subscriber
        if (
            pub_qos.durability == DurabilityPolicy.VOLATILE
            and sub_qos.durability == DurabilityPolicy.TRANSIENT_LOCAL
        ):
            return (
                False,
                f"Incompatible durability: publisher={pub_qos.durability}, subscriber={sub_qos.durability}",
            )

        return True, "Profiles are compatible"


# Global instance for easy access
_global_qos_manager: Optional[QoSManager] = None


def get_qos_manager() -> QoSManager:
    """
    Get global QoS manager instance.

    Returns:
        Global QoSManager instance.
    """
    global _global_qos_manager
    if _global_qos_manager is None:
        _global_qos_manager = QoSManager()
    return _global_qos_manager


def get_qos_profile(profile_name: str) -> QoSProfile:
    """
    Convenience function to get QoS profile.

    Args:
        profile_name: Name of the profile.

    Returns:
        QoSProfile for the requested profile.
    """
    return get_qos_manager().get(profile_name)
