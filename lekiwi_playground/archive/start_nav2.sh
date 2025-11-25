#!/bin/bash

# LeKiwi Nav2 Navigation Launcher
# Core + Nav2 자율 주행 시스템 실행

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   LeKiwi Nav2 Navigation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Always source the workspace setup
echo -e "${YELLOW}ROS2 workspace 환경 설정 중...${NC}"
cd ~/workspace/lerobot_ros2
source install/setup.bash

# Set environment variables (use FastRTPS to match Isaac Sim)
export ROS_DOMAIN_ID=10
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

echo -e "${GREEN}✓ 환경 변수 설정 완료${NC}"
echo "  ROS_DOMAIN_ID: $ROS_DOMAIN_ID"
echo "  RMW_IMPLEMENTATION: $RMW_IMPLEMENTATION"
echo ""

echo -e "${BLUE}실행 중인 노드:${NC}"
echo "  • Core nodes (robot_state_publisher, hardware_interface, command_arbiter)"
echo "  • base_controller (odometry)"
echo "  • Nav2 stack (planner, controller, behavior tree, etc.)"
echo ""

echo -e "${YELLOW}주의사항:${NC}"
echo "  1. Isaac Sim이 실행 중이고 Play 상태인지 확인하세요"
echo "  2. Map이 필요한 경우 map 파일을 준비하세요"
echo ""

echo -e "${BLUE}명령 우선순위:${NC}"
echo "  • Teleop (priority 200) → Nav2 override 가능"
echo "  • Nav2 (priority 100) → 기본 자율 주행"
echo ""

echo -e "${GREEN}Nav2 시스템을 시작합니다...${NC}"
echo ""

# Launch Nav2 system
ros2 launch lekiwi_bringup lekiwi_nav2.launch.py
