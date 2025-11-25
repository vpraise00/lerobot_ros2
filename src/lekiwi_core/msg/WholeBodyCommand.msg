# Unified command message for coordinated whole-body control
# Combines base velocity and arm joint commands

std_msgs/Header header

# Base velocity command (for mobile base)
geometry_msgs/Twist base_twist

# Arm joint commands
string[] arm_joint_names
float64[] arm_positions  # Target positions (rad)
float64[] arm_velocities # Target velocities (rad/s), optional (empty = position control only)
float64[] arm_efforts    # Target efforts (Nm), optional (empty = no effort control)

# Control mode flags
bool base_enabled  # If true, apply base_twist
bool arm_enabled   # If true, apply arm commands

# Priority level (0=lowest, 255=highest)
uint8 priority
