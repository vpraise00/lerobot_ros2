#!/usr/bin/env bash
# LeKiwi wheel teleop (all-in-one)
# - 백그라운드: KiwiBaseController (/cmd_vel -> /joint_command, odom/TF)
# - 포그라운드: teleop_twist_keyboard (/cmd_vel 발행)
# MoveIt2와 동시 사용 가능 (팔/바퀴 조인트 분리)

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

# Cleanup function
cleanup() {
  echo
  echo "[INFO] Shutting down..."
  if [ -n "${CONTROLLER_PID:-}" ]; then
    kill "${CONTROLLER_PID}" 2>/dev/null || true
    wait "${CONTROLLER_PID}" 2>/dev/null || true
  fi
  echo "[INFO] Done."
}
trap cleanup EXIT INT TERM

echo "[3/3] Starting KiwiBaseController (background)..."
ros2 run lekiwi_base_control lekiwi_kiwi_base_controller \
  --ros-args -p use_sim_time:=${USE_SIM_TIME} -p output_topic:=/joint_command &
CONTROLLER_PID=$!

sleep 1

echo
echo "========================================"
echo "  Keyboard Controls (teleop_twist_keyboard)"
echo "========================================"
echo "  i/k : forward / backward"
echo "  j/l : strafe left / right"
echo "  u/o : rotate CCW / CW"
echo "  space : stop"
echo "  q : quit"
echo "========================================"
echo

exec ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=/cmd_vel
