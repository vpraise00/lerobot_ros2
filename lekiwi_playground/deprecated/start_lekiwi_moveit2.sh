#!/bin/bash

set +u
set -eo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

: "${AMENT_TRACE_SETUP_FILES:=}"
if [ -n "$ROS_DISTRO" ] && [ -f "/opt/ros/$ROS_DISTRO/setup.bash" ]; then
  source "/opt/ros/$ROS_DISTRO/setup.bash"
elif [ -f /opt/ros/jazzy/setup.bash ]; then
  source /opt/ros/jazzy/setup.bash
fi
if [ -f "${WS_ROOT}/install/setup.bash" ]; then
  source "${WS_ROOT}/install/setup.bash"
fi

# Force CycloneDDS for unified RMW across all nodes.
export RMW_IMPLEMENTATION="rmw_cyclonedds_cpp"
echo "Starting MoveIt2 with RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION}"

LAUNCH_FILE="moveit_with_executor.launch.py"
if [[ "${1:-}" == "--legacy" ]]; then
  LAUNCH_FILE="moveit.launch.py"
  shift
fi

ros2 launch lekiwi_moveit2 "${LAUNCH_FILE}" "$@"
