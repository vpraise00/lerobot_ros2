# Comprehensive robot state message
# Fuses joint states, odometry, and sensor health

std_msgs/Header header

# Joint state information
sensor_msgs/JointState joint_state

# Odometry (base position and velocity)
nav_msgs/Odometry odometry

# Sensor health status
bool joint_states_healthy
bool odometry_healthy
bool cameras_healthy
float64 joint_states_age_sec  # Time since last joint state update
float64 odometry_age_sec      # Time since last odometry update

# Robot operation mode
uint8 OPERATION_MODE_IDLE = 0
uint8 OPERATION_MODE_NAVIGATION = 1
uint8 OPERATION_MODE_MANIPULATION = 2
uint8 OPERATION_MODE_COORDINATED = 3
uint8 OPERATION_MODE_EMERGENCY = 255
uint8 operation_mode

# Error flags
bool emergency_stop_active
bool collision_detected
bool joint_limit_violation
string status_message  # Human-readable status or error message
