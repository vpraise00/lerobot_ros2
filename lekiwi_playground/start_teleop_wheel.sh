#!/usr/bin/env bash
# LeKiwi wheel teleop (all-in-one)
# - 백그라운드: KiwiBaseController (/cmd_vel -> /wheel_command, odom/TF)
# - 포그라운드: teleop_twist_keyboard (/cmd_vel 발행)
# MoveIt2와 동시 사용 가능 (팔: /joint_command, 바퀴: /wheel_command)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "========================================"
echo "   LeKiwi Wheel Teleop (All-in-One)"
echo "========================================"
echo

if [ ! -f "${ROOT_DIR}/install/setup.bash" ]; then
  echo "[ERROR] ${ROOT_DIR}/install/setup.bash not found. Run 'colcon build' first."
  exit 1
fi

echo "[1/3] Loading ROS2 workspace: ${ROOT_DIR}"
set +u
source "${ROOT_DIR}/install/setup.bash"
set -u

USE_SIM_TIME=${USE_SIM_TIME:-false}

echo "[2/3] ROS_DOMAIN_ID: ${ROS_DOMAIN_ID:-<not set>} (must match Isaac Sim)"
echo "      USE_SIM_TIME: ${USE_SIM_TIME}"
echo

CONTROLLER_PID=""

# Cleanup function - kill controller process
cleanup() {
  echo
  echo "[INFO] Shutting down..."

  # Kill controller
  if [ -n "${CONTROLLER_PID:-}" ]; then
    echo "[INFO] Stopping controller (PID: $CONTROLLER_PID)..."
    kill -TERM "$CONTROLLER_PID" 2>/dev/null || true
    sleep 0.5
    kill -KILL "$CONTROLLER_PID" 2>/dev/null || true
  fi

  # Kill any orphaned processes from this script
  pkill -P $$ 2>/dev/null || true

  echo "[INFO] Done."
}

# Set trap for all exit signals
trap cleanup EXIT INT TERM QUIT HUP

echo "[3/3] Starting KiwiBaseController (background)..."
ros2 run lekiwi_base_control lekiwi_kiwi_base_controller \
  --ros-args -p use_sim_time:=${USE_SIM_TIME} -p output_topic:=/wheel_command &
CONTROLLER_PID=$!

sleep 1

# Verify controller started
if ! kill -0 "$CONTROLLER_PID" 2>/dev/null; then
  echo "[ERROR] Controller failed to start!"
  exit 1
fi

echo
echo "========================================"
echo "  Keyboard Controls (teleop_twist_keyboard)"
echo "========================================"
echo "  i/k : forward / backward"
echo "  j/l : strafe left / right"
echo "  u/o : rotate CCW / CW"
echo "  space : stop"
echo "  q or Ctrl+C : quit"
echo "========================================"
echo

# Run teleop in FOREGROUND (needs terminal access for keyboard input)
# When teleop exits, cleanup will be called via trap
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=/cmd_vel

# cleanup will be called automatically via trap
