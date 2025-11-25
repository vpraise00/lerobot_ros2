"""
Parameter Utilities for LeKiwi Robot

Provides standardized parameter handling and validation.
"""

from __future__ import annotations

from typing import Any, Optional

from rclpy.node import Node
from rclpy.parameter import Parameter


class ParameterValidator:
    """Validates and manages ROS2 parameters for LeKiwi nodes."""

    def __init__(self, node: Node):
        """
        Initialize parameter validator.

        Args:
            node: ROS2 node instance.
        """
        self.node = node

    def declare_and_get(
        self,
        name: str,
        default_value: Any,
        description: str = "",
        validator: Optional[callable] = None,
    ) -> Any:
        """
        Declare parameter and get its value with optional validation.

        Args:
            name: Parameter name.
            default_value: Default value if parameter not set.
            description: Parameter description for introspection.
            validator: Optional validation function that raises ValueError if invalid.

        Returns:
            Parameter value.

        Raises:
            ValueError: If validation fails.
        """
        # Declare parameter with description
        self.node.declare_parameter(name, default_value)

        # Get parameter value
        param = self.node.get_parameter(name)
        value = param.value

        # Validate if validator provided
        if validator is not None:
            try:
                validator(value)
            except ValueError as e:
                self.node.get_logger().error(
                    f"Parameter '{name}' validation failed: {e}"
                )
                raise

        self.node.get_logger().info(f"Parameter '{name}' = {value}")
        return value

    def get_required(self, name: str, description: str = "") -> Any:
        """
        Get required parameter, fails if not provided.

        Args:
            name: Parameter name.
            description: Parameter description.

        Returns:
            Parameter value.

        Raises:
            KeyError: If parameter not set.
        """
        if not self.node.has_parameter(name):
            error_msg = f"Required parameter '{name}' not provided. {description}"
            self.node.get_logger().error(error_msg)
            raise KeyError(error_msg)

        param = self.node.get_parameter(name)
        value = param.value
        self.node.get_logger().info(f"Required parameter '{name}' = {value}")
        return value

    @staticmethod
    def validate_positive(value: float) -> None:
        """Validate that value is positive."""
        if value <= 0:
            raise ValueError(f"Value must be positive, got {value}")

    @staticmethod
    def validate_non_negative(value: float) -> None:
        """Validate that value is non-negative."""
        if value < 0:
            raise ValueError(f"Value must be non-negative, got {value}")

    @staticmethod
    def validate_range(min_val: float, max_val: float) -> callable:
        """
        Create range validator.

        Args:
            min_val: Minimum allowed value.
            max_val: Maximum allowed value.

        Returns:
            Validator function.
        """

        def validator(value: float) -> None:
            if not (min_val <= value <= max_val):
                raise ValueError(f"Value {value} not in range [{min_val}, {max_val}]")

        return validator

    @staticmethod
    def validate_non_empty(value: str) -> None:
        """Validate that string is non-empty."""
        if not value or not value.strip():
            raise ValueError("String cannot be empty")

    @staticmethod
    def validate_list_length(expected_length: int) -> callable:
        """
        Create list length validator.

        Args:
            expected_length: Expected list length.

        Returns:
            Validator function.
        """

        def validator(value: list) -> None:
            if len(value) != expected_length:
                raise ValueError(
                    f"List length {len(value)} does not match expected {expected_length}"
                )

        return validator


def load_joint_config(node: Node, param_namespace: str = "joints") -> dict:
    """
    Load joint configuration from parameters.

    Expected parameters:
    - {param_namespace}.names: List of joint names
    - {param_namespace}.lower_limits: List of lower limits (optional)
    - {param_namespace}.upper_limits: List of upper limits (optional)
    - {param_namespace}.max_velocities: List of max velocities (optional)

    Args:
        node: ROS2 node instance.
        param_namespace: Parameter namespace for joint config.

    Returns:
        Dictionary with joint configuration.
    """
    validator = ParameterValidator(node)

    # Get joint names (required)
    joint_names = validator.get_required(f"{param_namespace}.names")

    num_joints = len(joint_names)

    # Get optional limits
    config = {"names": joint_names}

    # Try to get limits if specified
    if node.has_parameter(f"{param_namespace}.lower_limits"):
        config["lower_limits"] = node.get_parameter(f"{param_namespace}.lower_limits").value
    if node.has_parameter(f"{param_namespace}.upper_limits"):
        config["upper_limits"] = node.get_parameter(f"{param_namespace}.upper_limits").value
    if node.has_parameter(f"{param_namespace}.max_velocities"):
        config["max_velocities"] = node.get_parameter(f"{param_namespace}.max_velocities").value

    # Validate lengths if limits provided
    for key in ["lower_limits", "upper_limits", "max_velocities"]:
        if key in config:
            if len(config[key]) != num_joints:
                raise ValueError(
                    f"{key} length ({len(config[key])}) does not match joint count ({num_joints})"
                )

    return config
