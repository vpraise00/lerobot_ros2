#!/bin/bash

set +u
set -eo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

: "${AMENT_TRACE_SETUP_FILES:=}"
if [ -n "$ROS_DISTRO" ] && [ -f "/opt/ros/$ROS_DISTRO/setup.bash" ]; then
  # shellcheck disable=SC1090
  source "/opt/ros/$ROS_DISTRO/setup.bash"
elif [ -f /opt/ros/jazzy/setup.bash ]; then
  source /opt/ros/jazzy/setup.bash
fi
if [ -f "${WS_ROOT}/install/setup.bash" ]; then
  # shellcheck disable=SC1091
  source "${WS_ROOT}/install/setup.bash"
fi

# Force CycloneDDS for unified RMW across all nodes.
export RMW_IMPLEMENTATION="rmw_cyclonedds_cpp"
echo "Starting Bringup with RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION}"

ros2 launch lekiwi_bringup lekiwi_sim_bringup.launch.py "$@"
