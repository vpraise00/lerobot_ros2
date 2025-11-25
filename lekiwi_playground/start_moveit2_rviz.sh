#!/usr/bin/env bash
# RViz2 only (MoveIt MotionPlanning) launcher.
# Use after start_moveit2_isaac.sh is already running move_group + executor.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "========================================"
echo "   LeKiwi MoveIt2 RViz (Isaac Sim)"
echo "========================================"
echo

if [ ! -f "${ROOT_DIR}/install/setup.bash" ]; then
  echo "❌ ${ROOT_DIR}/install/setup.bash 가 없습니다. 먼저 colcon build를 실행하세요."
  exit 1
fi
echo "🔧 ROS2 워크스페이스 로드: ${ROOT_DIR}"
set +u
source "${ROOT_DIR}/install/setup.bash"
set -u

USE_SIM_TIME=${USE_SIM_TIME:-false}
echo "🌐 ROS_DOMAIN_ID: ${ROS_DOMAIN_ID:-<not set>} (Isaac과 동일해야 합니다)"
echo "🖼️  RViz2만 실행 (move_group은 이미 실행 중이어야 합니다)"

ros2 launch lekiwi_moveit2 rviz_only.launch.py use_sim_time:=${USE_SIM_TIME} "$@"
