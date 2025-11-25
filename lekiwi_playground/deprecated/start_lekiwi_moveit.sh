#!/bin/bash

# Helper to launch a minimal MoveIt stack for LeKiwi (planning/visualization).

set +u
set -eo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

: "${AMENT_TRACE_SETUP_FILES:=}"
if [ -f /opt/ros/jazzy/setup.bash ]; then
  # shellcheck disable=SC1091
  source /opt/ros/jazzy/setup.bash
fi
if [ -f "${WS_ROOT}/install/setup.bash" ]; then
  # shellcheck disable=SC1091
  source "${WS_ROOT}/install/setup.bash"
fi

LAUNCH_FILE="${WS_ROOT}/scripts/lekiwi/lekiwi_moveit.launch.py"

ros2 launch "${LAUNCH_FILE}" "$@"
