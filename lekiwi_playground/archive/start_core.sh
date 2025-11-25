#!/bin/bash

# LeKiwi Core System Launcher
# 핵심 노드만 실행: robot_state_publisher, hardware_interface, command_arbiter

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   LeKiwi Core System${NC}"
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
echo "  • robot_state_publisher"
echo "  • static_transform_publisher"
echo "  • hardware_interface"
echo "  • command_arbiter"
echo ""

echo -e "${YELLOW}Isaac Sim이 실행 중이고 Play 상태인지 확인하세요!${NC}"
echo ""
echo -e "${GREEN}Core 시스템을 시작합니다...${NC}"
echo ""

# Launch core system
ros2 launch lekiwi_bringup lekiwi_core.launch.py
