#!/usr/bin/env bash
# LeKiwi base keyboard teleop launcher (Isaac Sim)
# - Starts the Kiwi base controller (cmd_vel -> joint_command)
# - Keeps everything minimal: no MoveIt, no arbiter, no extra nodes
# - Run teleop_twist_keyboard in another terminal

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "========================================"
echo "   LeKiwi Base Teleop (Isaac Sim)"
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
echo "▶️  Isaac Sim에서 set_omnigraph_all.py 실행 후 Play 상태인지 확인하세요."
echo "⌨️  다른 터미널에서 키보드 텔레옵:"
echo "    ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel"
echo
echo "⚡ Kiwi base controller 실행 (/cmd_vel -> /joint_command, odom/TF 발행)"

exec ros2 run lekiwi_base_control lekiwi_kiwi_base_controller \
  --ros-args -p use_sim_time:=${USE_SIM_TIME} -p output_topic:=/joint_command "$@"
