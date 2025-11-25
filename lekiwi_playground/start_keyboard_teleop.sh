#!/usr/bin/env bash
# Keyboard teleop launcher for LeKiwi base (/cmd_vel publisher)
# - Sources the workspace and runs teleop_twist_keyboard with cmd_vel remap.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "========================================"
echo "   LeKiwi Keyboard Teleop (/cmd_vel)"
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

echo "🌐 ROS_DOMAIN_ID: ${ROS_DOMAIN_ID:-<not set>} (Isaac과 동일해야 합니다)"
echo "⌨️  키 입력: i/k(전후), j/l(좌우), u/o(회전 포함), 스페이스(정지), .(감속)"
echo

# Run teleop_twist_keyboard with /cmd_vel remap
exec ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel "$@"
