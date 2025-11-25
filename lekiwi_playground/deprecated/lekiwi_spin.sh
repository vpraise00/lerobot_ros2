#!/bin/bash

# Simple helper to run the LeKiwi spin demo publisher.
# Assumes this script is executed from anywhere inside the workspace.

# Disable nounset to avoid unbound-var errors in sourced setup files, keep errexit/pipefail.
set +u
set -eo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

# Prevent unbound variable errors inside ROS setup scripts.
: "${AMENT_TRACE_SETUP_FILES:=}"

# Source ROS2 and workspace overlays if available.
if [ -f /opt/ros/jazzy/setup.bash ]; then
  # shellcheck disable=SC1091
  source /opt/ros/jazzy/setup.bash
fi
if [ -f "${WS_ROOT}/install/setup.bash" ]; then
  # shellcheck disable=SC1091
  source "${WS_ROOT}/install/setup.bash"
fi

PYTHON_BIN=$(command -v python3 || true)
if [ -z "$PYTHON_BIN" ]; then
  echo "python3 not found in PATH" >&2
  exit 1
fi

"${PYTHON_BIN}" "${WS_ROOT}/scripts/lekiwi/lekiwi_spin_demo.py" "$@"
