"""
LeKiwi Core Package

Provides core functionality for the LeKiwi robot system:
- Custom messages (WholeBodyCommand, RobotState)
- QoS profile management
- Common utilities (parameters, TF helpers)
- Operation mode definitions
"""

__version__ = "1.0.0"

# Import utility modules for easy access
from . import qos
from . import parameters
from . import tf_helpers

__all__ = ["qos", "parameters", "tf_helpers"]
