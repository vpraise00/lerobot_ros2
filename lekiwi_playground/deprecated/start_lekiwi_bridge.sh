#!/bin/bash

# Helper to launch the LeKiwi Isaac bridge (Float64MultiArray -> JointState).
# Keeps style similar to other lerobot_ros2 helper scripts.

set -eo pipefail
set +u  # setup.bash may reference unset vars

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

# Default args
CONFIG_DEFAULT="${WS_ROOT}/install/lekiwi_isaac_bridge/share/lekiwi_isaac_bridge/config/lekiwi_sim.yaml"
INPUT_DEFAULT="/joint_commands"
OUTPUT_DEFAULT="/joint_command"

# Allow overrides via env or CLI
CONFIG_PATH="${CONFIG_PATH:-$CONFIG_DEFAULT}"
INPUT_TOPIC="${INPUT_TOPIC:-$INPUT_DEFAULT}"
OUTPUT_TOPIC="${OUTPUT_TOPIC:-$OUTPUT_DEFAULT}"

# Source ROS2 + workspace overlays
: "${AMENT_TRACE_SETUP_FILES:=}"
if [ -f /opt/ros/jazzy/setup.bash ]; then
  # shellcheck disable=SC1091
  source /opt/ros/jazzy/setup.bash
fi
if [ -f "${WS_ROOT}/install/setup.bash" ]; then
  # shellcheck disable=SC1091
  source "${WS_ROOT}/install/setup.bash"
fi

# Run bridge
ros2 run lekiwi_isaac_bridge bridge_node \
  --ros-args \
  -p config:="${CONFIG_PATH}" \
  -p input_topic:="${INPUT_TOPIC}" \
  -p output_topic:="${OUTPUT_TOPIC}"
