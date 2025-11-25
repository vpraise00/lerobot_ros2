#!/usr/bin/env bash
# LeKiwi MoveIt2 launcher for Isaac Sim
# - Assumes Isaac Sim has the OmniGraph from scripts/lekiwi/set_omnigraph_all.py running.
# - Starts MoveIt2 + trajectory executor that streams /joint_command JointStates to Isaac.

set -euo pipefail

# Resolve workspace root (repo root = parent of this script's dir)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "========================================"
echo "   LeKiwi MoveIt2 (Isaac Sim)"
echo "========================================"
echo

# Source workspace
if [ ! -f "${ROOT_DIR}/install/setup.bash" ]; then
  echo "❌ ${ROOT_DIR}/install/setup.bash 가 없습니다. 먼저 colcon build를 실행하세요."
  exit 1
fi
echo "🔧 ROS2 워크스페이스 로드: ${ROOT_DIR}"
# setup.bash 내부에서 COLCON_TRACE 등 미정 의존 변수가 있을 수 있으므로 일시적으로 -u 해제
set +u
source "${ROOT_DIR}/install/setup.bash"
set -u

# Show domain info (do not override)
echo "🌐 ROS_DOMAIN_ID: ${ROS_DOMAIN_ID:-<not set>} (Isaac과 동일해야 합니다)"
echo

echo "⚡ MoveIt2 + Trajectory Executor 실행"
echo "   Isaac Sim Script Editor에서 set_omnigraph_all.py를 실행하고 Play 상태인지 확인하세요."
echo "   (RViz2는 별도 스크립트로 실행)"
echo

# Default args (system time by default; set USE_SIM_TIME=true to use /clock)
USE_SIM_TIME=${USE_SIM_TIME:-false}
LAUNCH_RVIZ=${LAUNCH_RVIZ:-false}

ros2 launch lekiwi_moveit2 moveit_with_executor.launch.py \
  use_sim_time:=${USE_SIM_TIME} \
  launch_rviz:=${LAUNCH_RVIZ} \
  "$@"
