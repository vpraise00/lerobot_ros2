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

# Force CycloneDDS for Nav2 to avoid Fast-DDS shared memory/socket issues.
export RMW_IMPLEMENTATION="rmw_cyclonedds_cpp"
echo "Starting Nav2 with RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION}"

LAUNCH_FILE="lekiwi_nav2_with_kiwi.launch.py"
if [[ "${1:-}" == "--legacy" ]]; then
  LAUNCH_FILE="nav2.launch.py"
  shift
fi

# Append default use_sim_time when caller didn't override it.
EXTRA_ARGS=()
if ! printf '%s\n' "$@" | grep -q 'use_sim_time:='; then
  EXTRA_ARGS+=("use_sim_time:=true")
fi

ros2 launch lekiwi_nav2 "${LAUNCH_FILE}" "${EXTRA_ARGS[@]}" "$@"
