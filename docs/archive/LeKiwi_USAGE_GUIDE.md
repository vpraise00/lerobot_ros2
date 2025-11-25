# LeKiwi Mobile Manipulation System - 사용 가이드

LeKiwi 로봇을 Isaac Sim에서 Nav2와 MoveIt2로 제어하는 통합 가이드입니다.

## 📑 목차

1. [Quick Start](#quick-start) ⭐
2. [시스템 개요](#시스템-개요)
3. [환경 세팅](#환경-세팅)
4. [사용 방법](#사용-방법)
5. [Launch File 설명](#launch-file-설명)
6. [테스트 및 검증](#테스트-및-검증)
7. [문제 해결](#문제-해결)

---

## Quick Start

### 🚀 2개 터미널로 바로 시작하기

**Terminal 1: Nav2 실행**
```bash
cd ~/workspace/lerobot_ros2/lekiwi_playground
./start_nav2.sh
```

**Terminal 2: 로봇 제어**
```bash
source ~/workspace/lerobot_ros2/install/setup.bash

# 전진
ros2 topic pub /cmd_vel_nav geometry_msgs/Twist "{linear: {x: 0.2}}" -r 10

# 좌측 이동 (Kiwi drive!)
ros2 topic pub /cmd_vel_nav geometry_msgs/Twist "{linear: {y: 0.2}}" -r 10

# 회전
ros2 topic pub /cmd_vel_nav geometry_msgs/Twist "{angular: {z: 0.3}}" -r 10
```

### 📂 실행 스크립트 위치

```
lekiwi_playground/
├── start_core.sh       # 기본 시스템만
├── start_nav2.sh       # Nav2 자율 주행
└── start_moveit2.sh    # MoveIt2 암 제어
```

---

## 시스템 개요

### 아키텍처

```
┌─────────────── Isaac Sim ──────────────┐
│  ROS2 Action Graph                     │
│  • /joint_states (RELIABLE)      ────► │ ROS2
│  • /joint_command (RELIABLE)     ◄──── │
└────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
[Teleop]       [Nav2]         [MoveIt2]
Priority 200   Priority 100   Priority 150
    │               │               │
    └───────────────┼───────────────┘
                    ▼
        ┌─────────────────────┐
        │  Command Arbiter    │ ← 우선순위 기반 중재
        │  (lekiwi_command_   │
        │   arbiter)          │
        └──────────┬──────────┘
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
 /base_commands          /arm_commands
       │                       │
       └───────────┬───────────┘
                   ▼
        ┌──────────────────────┐
        │ Hardware Interface   │ ← 명령 통합
        │ (lekiwi_hardware_    │
        │  interface)          │
        └──────────┬───────────┘
                   ▼
            /joint_command
                   │
                   ▼
            Isaac Sim 로봇
```

### 주요 컴포넌트

| 컴포넌트 | 역할 | 파일 |
|----------|------|------|
| **Command Arbiter** | 우선순위 기반 명령 중재 | `lekiwi_command_arbiter` |
| **Hardware Interface** | 명령 통합 및 Isaac Sim 브리지 | `lekiwi_hardware` |
| **Base Controller** | Odometry 계산 및 발행 | `lekiwi_base_control` |
| **Nav2** | 자율 주행 | Nav2 stack |
| **MoveIt2** | 암 모션 플래닝 | MoveIt2 stack |

### 명령 우선순위

```
Emergency Stop  (255) ← 최우선
    ↓
Teleoperation   (200)
    ↓
Manipulation    (150) ← MoveIt2 arm commands
    ↓
Navigation      (100) ← Nav2 base commands
    ↓
Idle            (0)
```

**중요**: 높은 우선순위 명령이 낮은 우선순위를 항상 override합니다.

---

## 환경 세팅

### 1. 필수 환경 변수

```bash
export ROS_DOMAIN_ID=10
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

**자동 설정** (권장):
```bash
# ~/.bashrc에 추가
echo 'export ROS_DOMAIN_ID=10' >> ~/.bashrc
echo 'export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp' >> ~/.bashrc
source ~/.bashrc
```

### 2. 워크스페이스 빌드

```bash
cd /home/vpraise/workspace/lerobot_ros2
colcon build --symlink-install
source install/setup.bash
```

### 3. Isaac Sim 설정

#### Isaac Sim 실행
```bash
isaac-sim
```

#### Omnigraph 설정

**방법 1: 자동 스크립트 (권장)**
```python
# Isaac Sim Script Editor (Window → Script Editor)에서 실행
import sys
sys.path.append('/home/vpraise/workspace/lerobot_ros2/install/lekiwi_isaac_bridge/lib/python3.12/site-packages')

from lekiwi_isaac_bridge import setup_omnigraph
setup_omnigraph.main()
```

**방법 2: 수동 설정**
1. Window → Visual Scripting → Action Graph
2. New Action Graph 생성
3. 노드 추가:
   - `On Playback Tick`
   - `ROS2 Context` (domain_id: 10)
   - `ROS2 Subscribe Joint State` (topic: `/joint_command`, QoS: RELIABLE)
   - `Isaac Articulation Controller` (targetPrim: `/World/LeKiwi`)
   - `ROS2 Publish Joint State` (topic: `/joint_states`, QoS: RELIABLE, targetPrim: `/World/LeKiwi`)

자세한 내용: [README_OMNIGRAPH.md](README_OMNIGRAPH.md)

---

## 사용 방법

### 시나리오별 Launch 가이드

#### 시나리오 1: Core System Only (기본 테스트)

**필요 터미널: 2개**

```bash
# Terminal 1: Isaac Sim
isaac-sim
# USD 파일 로드 및 Play 버튼 클릭

# Terminal 2: Core 노드 실행
cd /home/vpraise/workspace/lerobot_ros2
source install/setup.bash
ros2 launch lekiwi_bringup lekiwi_core.launch.py
```

**포함 노드:**
- robot_state_publisher
- static_transform_publisher
- hardware_interface
- command_arbiter

**테스트:**
```bash
# Terminal 3: Teleop 명령
ros2 topic pub /cmd_vel_teleop geometry_msgs/Twist \
  "{linear: {x: 0.1, y: 0.0, z: 0.0}, angular: {z: 0.0}}" --once
```

---

#### 시나리오 2: Navigation (Nav2)

**필요 터미널: 2개**

```bash
# Terminal 1: Isaac Sim
isaac-sim

# Terminal 2: Nav2 + Core
cd /home/vpraise/workspace/lerobot_ros2
source install/setup.bash
ros2 launch lekiwi_bringup lekiwi_nav2.launch.py
```

**추가 포함 노드:**
- base_controller (odometry)
- Nav2 stack (planner_server, controller_server, bt_navigator, etc.)

**테스트:**
```bash
# RViz에서 "2D Goal Pose" 설정
# 또는 CLI로 목표 전송:
ros2 topic pub /goal_pose geometry_msgs/PoseStamped \
  "{header: {frame_id: 'map'}, pose: {position: {x: 1.0, y: 0.0, z: 0.0}}}" --once
```

---

#### 시나리오 3: Manipulation (MoveIt2)

**필요 터미널: 2개**

```bash
# Terminal 1: Isaac Sim
isaac-sim

# Terminal 2: MoveIt2 + Core
cd /home/vpraise/workspace/lerobot_ros2
source install/setup.bash
ros2 launch lekiwi_bringup lekiwi_moveit2.launch.py
```

**추가 포함 노드:**
- MoveIt2 move_group (현재 TODO - 설정 필요)

**테스트:**
```bash
# MoveIt RViz에서 Planning 수행
# 또는 Python API:
# (MoveIt2 설정 완료 후 사용 가능)
```

---

#### 시나리오 4: Mobile Manipulation (Nav2 + MoveIt2)

**필요 터미널: 2개** ⭐

```bash
# Terminal 1: Isaac Sim
isaac-sim

# Terminal 2: 통합 실행
cd /home/vpraise/workspace/lerobot_ros2
source install/setup.bash
ros2 launch lekiwi_bringup lekiwi_mobile_manip.launch.py
```

**모든 노드 포함:**
- Core (hardware_interface, command_arbiter, robot_state_publisher)
- base_controller (odometry)
- Nav2 (autonomous navigation)
- MoveIt2 (arm motion planning)

**사용 예시:**

```bash
# 동시 제어 테스트
# 1. Nav2로 base 이동
ros2 topic pub /cmd_vel_nav geometry_msgs/Twist \
  "{linear: {x: 0.1}}" -r 10 &

# 2. 동시에 arm teleop (priority 더 높음)
ros2 topic pub /arm_command_teleop sensor_msgs/JointState \
  "{name: ['STS3215_03a_v1_Revolute_45'], position: [0.5]}" --once

# Nav2는 계속 실행되고, arm 명령은 별도로 처리됨
```

**우선순위 동작:**
- Nav2 (priority 100)가 base를 이동
- 동시에 MoveIt2 (priority 150)가 arm을 제어
- Teleop (priority 200) 사용 시 둘 다 override
- Emergency stop (priority 255) 사용 시 모든 명령 중단

---

## Launch File 설명

### 1. `lekiwi_core.launch.py`

**목적**: 핵심 노드만 실행

**노드:**
- `robot_state_publisher` - URDF 기반 TF tree 발행
- `static_transform_publisher` - base_link ↔ base_plate_layer1_v5
- `hardware_interface` - Isaac Sim ↔ ROS2 브리지
- `command_arbiter` - 우선순위 기반 명령 중재

**사용:**
```bash
ros2 launch lekiwi_bringup lekiwi_core.launch.py
```

---

### 2. `lekiwi_nav2.launch.py`

**목적**: 자율 주행 시스템

**추가 노드:**
- `base_controller` - Odometry 계산/발행
- Nav2 stack - 자율 주행

**설정 파일:**
- `/config/kiwi_drive_controller.yaml` - Kiwi drive 최적화 파라미터

**특징:**
- Omnidirectional movement (vy_samples: 20)
- DWB local planner
- Costmap for obstacle avoidance

**사용:**
```bash
ros2 launch lekiwi_bringup lekiwi_nav2.launch.py

# Custom map 사용:
ros2 launch lekiwi_bringup lekiwi_nav2.launch.py map:=/path/to/map.yaml
```

---

### 3. `lekiwi_moveit2.launch.py`

**목적**: 암 모션 플래닝

**추가 노드:**
- MoveIt2 move_group (TODO - 설정 필요)

**현재 상태:**
- Core 노드만 실행
- MoveIt2 설정 파일 생성 필요

**사용:**
```bash
ros2 launch lekiwi_bringup lekiwi_moveit2.launch.py
```

---

### 4. `lekiwi_mobile_manip.launch.py`

**목적**: Mobile manipulation (base + arm 통합 제어)

**모든 노드 포함:**
- Core nodes
- base_controller
- Nav2 stack
- MoveIt2 move_group (TODO)

**특징:**
- Nav2와 MoveIt2 동시 실행
- Command arbiter가 우선순위 관리
- Base는 Nav2, Arm은 MoveIt2 제어

**사용:**
```bash
ros2 launch lekiwi_bringup lekiwi_mobile_manip.launch.py
```

---

## 테스트 및 검증

### 1. Topics 확인

```bash
# 모든 토픽 확인
ros2 topic list

# 기대되는 토픽:
# - /joint_states (Isaac Sim → ROS2)
# - /joint_command (ROS2 → Isaac Sim)
# - /cmd_vel_teleop (Teleop → Command Arbiter)
# - /cmd_vel_nav (Nav2 → Command Arbiter)
# - /arm_command_teleop (Arm Teleop → Command Arbiter)
# - /base_commands (Command Arbiter → Hardware Interface)
# - /arm_commands (Command Arbiter → Hardware Interface)
# - /odom (Base Controller → Nav2)
```

### 2. Nodes 확인

```bash
ros2 node list

# 기대되는 노드 (core):
# - /lekiwi_state_publisher
# - /lekiwi_hardware_interface
# - /lekiwi_command_arbiter

# Nav2 추가 시:
# - /lekiwi_base_controller
# - /controller_server
# - /planner_server
# - /bt_navigator
# - ...
```

### 3. TF Tree 확인

```bash
# TF 프레임 확인
ros2 run tf2_tools view_frames

# 기대되는 TF:
# map → odom → base_plate_layer1_v5 → (로봇 링크들)
```

### 4. 기능 테스트

#### Teleop 테스트
```bash
# Forward movement
ros2 topic pub /cmd_vel_teleop geometry_msgs/Twist \
  "{linear: {x: 0.2}}" -r 10

# Sideways (kiwi drive)
ros2 topic pub /cmd_vel_teleop geometry_msgs/Twist \
  "{linear: {y: 0.2}}" -r 10

# Rotation
ros2 topic pub /cmd_vel_teleop geometry_msgs/Twist \
  "{angular: {z: 0.5}}" -r 10
```

#### Nav2 테스트
```bash
# RViz 실행
rviz2

# 2D Goal Pose 설정하여 Nav2 테스트
```

#### 우선순위 테스트
```bash
# Nav2 실행 중
ros2 topic pub /cmd_vel_nav geometry_msgs/Twist \
  "{linear: {x: 0.1}}" -r 10 &

# Teleop으로 override (priority 200 > 100)
ros2 topic pub /cmd_vel_teleop geometry_msgs/Twist \
  "{linear: {x: 0.3}}" -r 10

# → Teleop 명령이 우선됨
```

---

## 문제 해결

### 문제 1: Isaac Sim에서 토픽이 보이지 않음

**원인**: QoS mismatch 또는 domain_id 불일치

**해결:**
```bash
# 1. ROS_DOMAIN_ID 확인
echo $ROS_DOMAIN_ID  # 10이어야 함

# 2. Isaac Sim omnigraph Context 노드 확인
# domain_id: 10

# 3. QoS 확인
# /joint_states: RELIABLE
# /joint_command: RELIABLE
```

### 문제 2: 로봇이 명령에 반응하지 않음

**원인**: Hardware interface 또는 command arbiter 미실행

**해결:**
```bash
# 노드 상태 확인
ros2 node list | grep -E "(hardware|arbiter)"

# 로그 확인
ros2 topic echo /base_commands
ros2 topic echo /joint_command

# 재시작
ros2 launch lekiwi_bringup lekiwi_core.launch.py
```

### 문제 3: Nav2가 작동하지 않음

**원인**: Odometry 미발행 또는 costmap 설정 오류

**해결:**
```bash
# Odometry 확인
ros2 topic echo /odom

# Base controller 실행 확인
ros2 node list | grep base_controller

# Nav2 로그 확인
ros2 topic echo /diagnostics
```

### 문제 4: 우선순위가 예상대로 작동하지 않음

**원인**: Command timeout 또는 topic 이름 오류

**해결:**
```bash
# Command arbiter 로그 확인
# (실행 시 터미널 출력 확인)

# Topic 이름 확인
ros2 topic list | grep cmd_vel

# 올바른 topic:
# - /cmd_vel_teleop (priority 200)
# - /cmd_vel_nav (priority 100)
# 잘못된 topic: /cmd_vel (작동 안 함)
```

---

## 다음 단계

### MoveIt2 설정 (TODO)

1. **MoveIt2 config 생성:**
   ```bash
   ros2 run moveit_setup_assistant moveit_setup_assistant
   ```

2. **URDF 로드:**
   - LeKiwi URDF 선택
   - Planning group 설정 (arm)
   - End-effector 설정

3. **Launch file 업데이트:**
   - `lekiwi_moveit2.launch.py`에 move_group 추가
   - `lekiwi_mobile_manip.launch.py`에 통합

4. **테스트:**
   ```bash
   ros2 launch lekiwi_bringup lekiwi_moveit2.launch.py
   ```

### 추가 기능

- [ ] Behavior tree for complex tasks
- [ ] Whole-body planning (MoveIt2 + Nav2 coordinated)
- [ ] Teleoperation GUI
- [ ] Safety monitoring
- [ ] Multi-robot coordination

---

## 참고 문서

- [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md) - 전체 시스템 설정
- [README_OMNIGRAPH.md](README_OMNIGRAPH.md) - Isaac Sim omnigraph 상세 가이드
- [구현_완료_요약.md](구현_완료_요약.md) - 구현 완료 사항 (한국어)
- [kiwi_drive_controller.yaml](../src/lekiwi_nav2/config/kiwi_drive_controller.yaml) - Nav2 설정 파일

---

## 요약

### 최소 터미널 구성

| 시나리오 | 터미널 수 | 명령 |
|----------|-----------|------|
| Core 테스트 | 2개 | `isaac-sim` + `lekiwi_core.launch.py` |
| Nav2 | 2개 | `isaac-sim` + `lekiwi_nav2.launch.py` |
| MoveIt2 | 2개 | `isaac-sim` + `lekiwi_moveit2.launch.py` |
| Mobile Manip | 2개 | `isaac-sim` + `lekiwi_mobile_manip.launch.py` |

### 핵심 Topic 맵

```
Input Topics (User → System):
  /cmd_vel_teleop       → Command Arbiter (priority 200)
  /cmd_vel_nav          → Command Arbiter (priority 100)
  /arm_command_teleop   → Command Arbiter (priority 200)
  /emergency_stop       → Command Arbiter (priority 255)

Internal Topics (System):
  /base_commands        → Hardware Interface
  /arm_commands         → Hardware Interface
  /joint_command        → Isaac Sim

Output Topics (System → User/Nav2):
  /joint_states         → robot_state_publisher, base_controller
  /odom                 → Nav2
  /tf, /tf_static       → All nodes
```

### 환경 변수 체크리스트

```bash
✓ ROS_DOMAIN_ID=10
✓ RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
✓ source /home/vpraise/workspace/lerobot_ros2/install/setup.bash
```

---

**완료!** 🎉 이제 LeKiwi 로봇으로 mobile manipulation을 시작할 수 있습니다!
