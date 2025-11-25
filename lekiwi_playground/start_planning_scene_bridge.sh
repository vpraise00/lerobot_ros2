#!/usr/bin/env bash
# Run the planning scene QoS bridge (volatile -> transient_local) so RViz can receive the planning scene.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ ! -f "${ROOT_DIR}/install/setup.bash" ]; then
  echo "❌ ${ROOT_DIR}/install/setup.bash 가 없습니다. 먼저 colcon build를 실행하세요."
  exit 1
fi

echo "🔧 ROS2 워크스페이스 로드: ${ROOT_DIR}"
set +u
source "${ROOT_DIR}/install/setup.bash"
set -u

echo "🌐 ROS_DOMAIN_ID: ${ROS_DOMAIN_ID:-<not set>} (Isaac과 동일해야 합니다)"
echo "▶️ planning scene QoS bridge 실행 중 (/monitored_planning_scene volatile -> transient_local)"

exec ros2 run lekiwi_moveit2 planning_scene_qos_bridge "$@"
