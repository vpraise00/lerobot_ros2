# LeKiwi 완전 설정 가이드

LeKiwi 로봇의 Isaac Sim + ROS2 통합을 위한 완전한 설정 가이드입니다.

## 목차

1. [시스템 아키텍처](#시스템-아키텍처)
2. [빠른 시작](#빠른-시작)
3. [상세 구성 요소](#상세-구성-요소)
4. [런치 파일 가이드](#런치-파일-가이드)
5. [Nav2 설정](#nav2-설정)
6. [MoveIt2 설정](#moveit2-설정)
7. [문제 해결](#문제-해결)

## 시스템 아키텍처

```
┌─────────────── Isaac Sim ───────────────┐
│                                          │
│  LeKiwi Robot USD Scene                 │
│         │                                │
│         ▼                                │
│  ROS2 Action Graph                      │
│  - Publish /joint_states (RELIABLE)     │
│  - Subscribe /joint_command (RELIABLE)  │
│  - Publish /clock                       │
│                                          │
└──────────────┬───────────────────────────┘
               │ ROS2 Topics
               │ (ROS_DOMAIN_ID=10)
               │
┌──────────────▼───────────────────────────┐
│          ROS2 노드들                      │
│                                          │
│  lekiwi_hardware_interface               │
│  - Subscribe: /joint_states              │
│  - Subscribe: /base_commands             │
│  - Subscribe: /arm_commands              │
│  - Publish: /joint_command               │
│                                          │
│  lekiwi_command_arbiter                  │
│  - Subscribe: /cmd_vel_teleop (우선순위 200)│
│  - Subscribe: /cmd_vel_nav (우선순위 100)  │
│  - Subscribe: /arm_command_teleop (150)  │
│  - Subscribe: /emergency_stop (255)      │
│  - Publish: /base_commands               │
│  - Publish: /arm_commands                │
│                                          │
│  lekiwi_base_controller                  │
│  - Subscribe: /cmd_vel                   │
│  - Subscribe: /joint_states              │
│  - Publish: /odom                        │
│  - Publish TF: odom → base_link          │
│                                          │
│  robot_state_publisher                   │
│  - Subscribe: /joint_states (RELIABLE)   │
│  - Publish TF: base_link → links         │
│                                          │
└──────────────────────────────────────────┘
```

## 빠른 시작

### 1. 빌드

```bash
cd /home/vpraise/workspace/lerobot_ros2
colcon build --symlink-install
source install/setup.bash
```

### 2. 환경 설정

```bash
export ROS_DOMAIN_ID=10
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_LOCALHOST_ONLY=0
```

### 3. Isaac Sim 설정

**Isaac Sim에서**:

1. USD 씬 열기: `/home/vpraise/Downloads/lekiwi_1120.usd`

2. Python Script Editor에서 실행:
   ```python
   import sys
   sys.path.append('/home/vpraise/workspace/lerobot_ros2/install/lekiwi_isaac_bridge/lib/python3.12/site-packages')

   from lekiwi_isaac_bridge import setup_omnigraph
   setup_omnigraph.main()
   ```

3. Action Graph 설정:
   - Window → Visual Scripting → Action Graph
   - ArticulationController 노드 선택
   - targetPrim: `/World/LeKiwi`
   - PublishJointState 노드 선택
   - targetPrim: `/World/LeKiwi`

4. Play 버튼 클릭

### 4. ROS2 노드 실행

**터미널 1: 기본 시스템**
```bash
source install/setup.bash
export ROS_DOMAIN_ID=10

ros2 launch lekiwi_bringup lekiwi_sim_bringup.launch.py
```

**터미널 2: 하드웨어 인터페이스**
```bash
source install/setup.bash
export ROS_DOMAIN_ID=10

ros2 run lekiwi_hardware hardware_interface
```

**터미널 3: 명령 중재자**
```bash
source install/setup.bash
export ROS_DOMAIN_ID=10

ros2 run lekiwi_command_arbiter command_arbiter
```

**터미널 4: 베이스 컨트롤러 (선택사항)**
```bash
source install/setup.bash
export ROS_DOMAIN_ID=10

ros2 run lekiwi_base_control base_controller_node
```

### 5. 테스트

**로봇 이동 테스트**:
```bash
# 원격 조작 (최고 우선순위)
ros2 topic pub /cmd_vel_teleop geometry_msgs/Twist "{linear: {x: 0.1}, angular: {z: 0.0}}" --once

# 오도메트리 확인
ros2 topic echo /odom

# TF 트리 확인
ros2 run tf2_tools view_frames
```

## 상세 구성 요소

### lekiwi_hardware_interface

**역할**: Isaac Sim과 ROS2 컨트롤러를 연결하는 하드웨어 추상화 계층

**구독 토픽**:
- `/joint_states` (sensor_msgs/JointState): Isaac Sim의 현재 관절 상태
- `/base_commands` (sensor_msgs/JointState): 베이스 휠 명령
- `/arm_commands` (sensor_msgs/JointState): 암 관절 명령

**발행 토픽**:
- `/joint_command` (sensor_msgs/JointState): 통합된 관절 명령 → Isaac Sim

**코드 위치**: `src/lekiwi_hardware/lekiwi_hardware/hardware_interface.py`

### lekiwi_command_arbiter

**역할**: 우선순위 기반 명령 중재

**우선순위**:
1. 비상 정지: 255
2. 원격 조작: 200
3. 매니퓰레이션: 150
4. 내비게이션: 100
5. 대기: 0

**구독 토픽**:
- `/emergency_stop` (std_msgs/Bool)
- `/cmd_vel_teleop` (geometry_msgs/Twist)
- `/arm_command_teleop` (sensor_msgs/JointState)
- `/cmd_vel_nav` (geometry_msgs/Twist)

**발행 토픽**:
- `/base_commands` (sensor_msgs/JointState): 베이스 휠 속도
- `/arm_commands` (sensor_msgs/JointState): 암 관절 명령

**특징**:
- 키위 드라이브 역기구학 내장
- 명령 타임아웃 (기본 0.5초)
- 우선순위 자동 선택

**코드 위치**: `src/lekiwi_command_arbiter/lekiwi_command_arbiter/command_arbiter.py`

### lekiwi_base_controller

**역할**: cmd_vel을 휠 속도로 변환 + 오도메트리 계산

**구독 토픽**:
- `/cmd_vel` (geometry_msgs/Twist): 베이스 속도 명령
- `/joint_states` (sensor_msgs/JointState): 실제 휠 속도 (오도메트리용)

**발행 토픽**:
- `/joint_command` (sensor_msgs/JointState): 휠 명령
- `/odom` (nav_msgs/Odometry): 오도메트리 정보

**TF 브로드캐스트**:
- `odom` → `base_plate_layer1_v5`

**특징**:
- 키위 드라이브 순/역 기구학
- 실시간 오도메트리 적분
- 공분산 행렬 포함

**코드 위치**: `src/lekiwi_base_control/lekiwi_base_control/base_controller_node.py`

## 런치 파일 가이드

### 기본 실행: lekiwi_sim_bringup.launch.py

**실행**:
```bash
ros2 launch lekiwi_bringup lekiwi_sim_bringup.launch.py
```

**포함 노드**:
- robot_state_publisher: URDF → TF 변환
- static_transform_publisher: base_link → base_plate_layer1_v5
- (선택) lekiwi_isaac_bridge: Float64MultiArray → JointState 변환

**파라미터**:
- `use_sim_time:=true` (기본값)
- `start_bridge:=false` (기존 브리지 비활성화 권장)

### 모듈식 실행 (권장)

각 구성 요소를 별도 터미널에서 실행하여 디버깅 용이:

```bash
# 터미널 1: 상태 퍼블리셔
ros2 launch lekiwi_bringup lekiwi_sim_bringup.launch.py

# 터미널 2: 하드웨어 인터페이스
ros2 run lekiwi_hardware hardware_interface

# 터미널 3: 명령 중재자
ros2 run lekiwi_command_arbiter command_arbiter

# 터미널 4: (선택) 베이스 컨트롤러
ros2 run lekiwi_base_control base_controller_node
```

## Nav2 설정

### 키위 드라이브 설정

**특징**:
- 전방향 이동 (omnidirectional)
- 3개 바퀴 (0°, 120°, 240° 배치)
- 바퀴 반지름: 0.055m
- 베이스 반지름: 0.25m

### 권장 Nav2 파라미터

```yaml
# controller_server 파라미터
controller_server:
  ros__parameters:
    controller_frequency: 20.0
    min_x_velocity_threshold: 0.001
    min_y_velocity_threshold: 0.001
    min_theta_velocity_threshold: 0.001

    FollowPath:
      plugin: "dwb_core::DWBLocalPlanner"
      min_vel_x: -0.3
      max_vel_x: 0.3
      min_vel_y: -0.3
      max_vel_y: 0.3
      max_vel_theta: 1.0
      min_speed_xy: 0.0
      max_speed_xy: 0.4
      min_speed_theta: 0.0

      # 키위 드라이브는 전방향 이동 가능
      acc_lim_x: 2.5
      acc_lim_y: 2.5
      acc_lim_theta: 3.2
      decel_lim_x: -2.5
      decel_lim_y: -2.5
      decel_lim_theta: -3.2

      # 경로 추적
      xy_goal_tolerance: 0.05
      yaw_goal_tolerance: 0.1

# costmap 설정
local_costmap:
  local_costmap:
    ros__parameters:
      update_frequency: 5.0
      publish_frequency: 2.0
      global_frame: odom
      robot_base_frame: base_plate_layer1_v5
      rolling_window: true
      width: 3
      height: 3
      resolution: 0.05
      robot_radius: 0.30  # 베이스 반지름 + 여유

      plugins: ["voxel_layer", "inflation_layer"]
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
        cost_scaling_factor: 3.0
        inflation_radius: 0.55
      voxel_layer:
        plugin: "nav2_costmap_2d::VoxelLayer"
        enabled: True
        publish_voxel_map: True
        origin_z: 0.0
        z_resolution: 0.05
        z_voxels: 16
        max_obstacle_height: 2.0
        mark_threshold: 0
        observation_sources: camera
        camera:
          data_type: "PointCloud2"
          topic: /camera/depth/points
          marking: true
          clearing: true
```

### Nav2 실행

```bash
# Nav2 실행
ros2 launch lekiwi_nav2 lekiwi_nav2_with_kiwi.launch.py use_sim_time:=true

# RViz에서 목표 설정
# 2D Goal Pose 도구 사용
```

## MoveIt2 설정

### 카메라 통합

LeKiwi는 2개의 카메라를 가지고 있습니다:
- `Camera_Model_v5`: 그리퍼 카메라 (end-effector 근처)
- `Camera_Model_v5_1`: 베이스 카메라

**Octomap 통합**:

```yaml
# moveit_cpp.yaml에 추가
sensors:
  - sensor_plugin: occupancy_map_monitor/PointCloudOctomapUpdater
    point_cloud_topic: /camera/depth/points
    max_range: 5.0
    point_subsample: 1
    padding_offset: 0.1
    padding_scale: 1.0
    max_update_rate: 1.0
    filtered_cloud_topic: filtered_cloud
```

### 전신 모션 플래닝

**SRDF 설정** (이미 구성됨):

```xml
<!-- src/lekiwi_description/srdf/lekiwi.srdf -->
<group name="whole_body">
  <group name="base" />
  <group name="arm" />
</group>
```

**MoveIt2 설정**:

```python
# Python 예제
from moveit_msgs.msg import MoveGroupAction
from geometry_msgs.msg import PoseStamped

# whole_body 그룹으로 플래닝
move_group = MoveGroupInterface("whole_body", "base_plate_layer1_v5")

# 목표 설정
pose_goal = PoseStamped()
pose_goal.header.frame_id = "base_plate_layer1_v5"
pose_goal.pose.position.x = 0.4
pose_goal.pose.position.y = 0.0
pose_goal.pose.position.z = 0.2
pose_goal.pose.orientation.w = 1.0

move_group.set_pose_target(pose_goal, "moving_jaw_named_v1_4")
move_group.go(wait=True)
```

## 문제 해결

### 1. /joint_states 토픽이 안 보임

**원인**: QoS 불일치 또는 Isaac Sim 미실행

**해결**:
```bash
# QoS 확인
ros2 topic info /joint_states -v

# Isaac Sim omnigraph 재확인
# - PublishJointState의 qosProfile이 RELIABLE인지 확인
# - targetPrim이 /World/LeKiwi로 설정되었는지 확인
```

### 2. TF 트리가 비어있음

**원인**: robot_state_publisher QoS 불일치

**해결**:
```bash
# robot_state_publisher 재시작 with QoS overrides
# lekiwi_sim_bringup.launch.py에 이미 포함됨

# 확인
ros2 run tf2_tools view_frames
evince frames.pdf
```

### 3. 로봇이 명령을 받지 않음

**원인**: 명령 우선순위 또는 타임아웃

**해결**:
```bash
# 중재자 로그 확인
ros2 topic echo /base_commands
ros2 topic echo /arm_commands

# 비상 정지 해제
ros2 topic pub /emergency_stop std_msgs/Bool "data: false" --once

# 텔레옵으로 직접 테스트 (최고 우선순위)
ros2 topic pub /cmd_vel_teleop geometry_msgs/Twist "{linear: {x: 0.1}}"
```

### 4. 오도메트리가 drift됨

**원인**: 키위 드라이브 파라미터 미세 조정 필요

**해결**:
```bash
# base_controller_node 파라미터 조정
ros2 param set /lekiwi_kiwi_base_controller wheel_radius 0.055
ros2 param set /lekiwi_kiwi_base_controller base_radius 0.25

# 또는 launch 파일에서:
# parameters=[{
#   'wheel_radius': 0.055,
#   'base_radius': 0.25,
# }]
```

### 5. Nav2가 장애물을 인식 못함

**원인**: 카메라 데이터 미통합

**해결**:
```bash
# 카메라 토픽 확인
ros2 topic list | grep camera
ros2 topic echo /camera/depth/points --no-arr

# costmap 설정에서 observation_sources 확인
# local_costmap.yaml의 camera 설정 검증
```

## 관련 문서

- [Isaac Sim Omnigraph 설정](README_OMNIGRAPH.md)
- [Isaac Sim 통합 가이드](ISAAC_SIM_INTEGRATION.md)
- [스크립트 레퍼런스](SCRIPTS_REFERENCE.md)

## 주요 파일 위치

```
lerobot_ros2/
├── src/
│   ├── lekiwi_hardware/
│   │   └── lekiwi_hardware/
│   │       └── hardware_interface.py
│   ├── lekiwi_command_arbiter/
│   │   └── lekiwi_command_arbiter/
│   │       └── command_arbiter.py
│   ├── lekiwi_base_control/
│   │   └── lekiwi_base_control/
│   │       └── base_controller_node.py
│   ├── lekiwi_description/
│   │   ├── urdf/lekiwi.urdf
│   │   └── srdf/lekiwi.srdf
│   ├── lekiwi_bringup/
│   │   └── launch/
│   │       └── lekiwi_sim_bringup.launch.py
│   └── lekiwi_core/
│       ├── msg/
│       │   ├── WholeBodyCommand.msg
│       │   └── RobotState.msg
│       └── config/
│           └── qos_profiles.yaml
└── docs/
    ├── COMPLETE_SETUP_GUIDE.md (이 문서)
    ├── README_OMNIGRAPH.md
    └── ISAAC_SIM_INTEGRATION.md
```

## 다음 단계

1. **현재 시스템 테스트**: 위의 빠른 시작 가이드로 기본 동작 확인
2. **Nav2 통합**: Nav2 파라미터 파일 생성 및 튜닝
3. **MoveIt2 통합**: whole_body 플래닝 테스트
4. **고급 기능**: 카메라 기반 장애물 회피, 조작 중 베이스 이동 등

## 문의

문제가 발생하면 다음을 확인하세요:
1. `ROS_DOMAIN_ID=10` 모든 터미널에서 설정되었는지
2. Isaac Sim Play 버튼이 눌러졌는지
3. `ros2 topic list`로 모든 토픽이 보이는지
4. `ros2 node list`로 모든 노드가 실행 중인지
