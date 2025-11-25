#!/bin/bash

# LeKiwi MoveIt2 Manipulation Launcher
# Core + MoveIt2 암 모션 플래닝 실행

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   LeKiwi MoveIt2 Manipulation${NC}"
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
echo "  • MoveIt2 move_group (TODO - 설정 필요)"
echo ""

echo -e "${YELLOW}주의사항:${NC}"
echo "  1. Isaac Sim이 실행 중이고 Play 상태인지 확인하세요"
echo "  2. MoveIt2 설정이 아직 완료되지 않았습니다"
echo ""

echo -e "${BLUE}명령 우선순위:${NC}"
echo "  • Teleop (priority 200) → MoveIt2 override 가능"
echo "  • MoveIt2 (priority 150) → 암 모션 플래닝"
echo ""

echo -e "${GREEN}MoveIt2 시스템을 시작합니다...${NC}"
echo ""

# Launch MoveIt2 system
ros2 launch lekiwi_bringup lekiwi_moveit2.launch.py
