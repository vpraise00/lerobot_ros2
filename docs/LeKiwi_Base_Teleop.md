# LeKiwi Base Keyboard Teleop (Isaac Sim)

LeKiwi 3륜 베이스(Kiwi Drive)를 키보드로 움직이는 가이드입니다. MoveIt2와 동시 사용이 가능합니다.

## 준비

### 1. URDF Import 설정 (중요!)

Isaac Sim에서 LeKiwi URDF를 import할 때 **바퀴 조인트는 Velocity Drive**로 설정해야 합니다.

| 조인트 타입 | Drive Mode | 이유 |
|------------|------------|------|
| 팔 조인트 (revolute) | Position | 정밀한 각도 제어 |
| 바퀴 조인트 (continuous) | **Velocity** | 연속 회전, PhysX ±2π 제한 회피 |

> Position Drive로 설정하면 `PhysX error: setDriveTarget() only supports target angle in range [-2Pi, 2Pi]` 에러가 발생합니다.

### 2. 환경 설정

```bash
# ROS2 환경
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=10  # Isaac Sim과 동일하게
source ~/workspace/lerobot_ros2/install/setup.bash

# 패키지 설치 (최초 1회)
sudo apt install ros-jazzy-teleop-twist-keyboard
```

### 3. Isaac Sim 설정

1. URDF import (바퀴는 Velocity Drive)
2. Script Editor에서 OmniGraph 설정:
   ```python
   exec(open("/home/vpraise/workspace/lerobot_ros2/scripts/lekiwi/set_omnigraph_all.py").read())
   ```
3. Play 상태로 전환

## 실행

```bash
./lekiwi_playground/start_teleop_wheel.sh
```

컨트롤러와 키보드 텔레옵이 하나의 스크립트로 실행됩니다. Ctrl+C로 종료하면 백그라운드 프로세스도 자동 정리됩니다.

## 키보드 조작

| 키 | 동작 |
|----|------|
| `i` / `k` | 전진 / 후진 |
| `j` / `l` | 좌측 / 우측 스트레이프 |
| `u` / `o` | 반시계 / 시계 회전 |
| `space` | 정지 |
| `.` | 감속 |
| `q` | 종료 |

## MoveIt2와 동시 사용

팔(arm)과 베이스(wheel)를 동시에 제어할 수 있습니다:

```bash
# 터미널 1: MoveIt2 (팔 제어)
./lekiwi_playground/start_moveit2_isaac.sh

# 터미널 2: 베이스 텔레옵 (바퀴 제어)
./lekiwi_playground/start_teleop_wheel.sh
```

두 시스템 모두 `/joint_command` 토픽을 사용하지만, **조인트 이름이 다르므로 충돌 없이 동작**합니다:
- MoveIt2: `STS3215_*` (팔 6개 조인트)
- Base Teleop: `ST3215_Servo_Motor_*` (바퀴 3개 조인트)

## 데이터 흐름

```
[키보드 입력]
     ↓
teleop_twist_keyboard
     ↓
/cmd_vel (geometry_msgs/Twist)
     ↓
KiwiBaseController (역기구학)
     ↓
/joint_command (sensor_msgs/JointState, velocity only)
     ↓
Isaac Sim OmniGraph → ArticulationController
     ↓
바퀴 회전 + /joint_states 피드백
     ↓
KiwiBaseController (순기구학)
     ↓
/odom + TF (odom → base_plate_layer1_v5)
```

## 확인 명령

```bash
# Isaac → ROS 토픽 확인
ros2 topic echo /joint_states

# 베이스 명령 확인
ros2 topic echo /joint_command

# Odometry 확인
ros2 topic echo /odom

# TF 확인
ros2 run tf2_tools view_frames
```

## 트러블슈팅

### PhysX ±2π 에러가 발생하는 경우

```
PhysX error: setDriveTarget() only supports target angle in range [-2Pi, 2Pi]
```

**원인**: 바퀴 조인트가 Position Drive로 설정됨

**해결**:
1. URDF 재import 시 바퀴를 Velocity Drive로 설정
2. 또는 런타임에 스크립트로 변경:
   ```python
   exec(open("/home/vpraise/workspace/lerobot_ros2/scripts/lekiwi/set_wheel_velocity_drive.py").read())
   ```

### 바퀴가 움직이지 않는 경우

1. `ROS_DOMAIN_ID` 확인 (Isaac과 동일해야 함)
2. Isaac Sim이 Play 상태인지 확인
3. OmniGraph 설정 확인:
   ```bash
   ros2 topic echo /joint_states  # 메시지가 와야 함
   ```
4. OmniGraph 재설정:
   ```python
   exec(open("/home/vpraise/workspace/lerobot_ros2/scripts/lekiwi/set_omnigraph_all.py").read())
   ```

### 시뮬레이션 시간 사용

Isaac `/clock`을 사용하려면:
```bash
USE_SIM_TIME=true ./lekiwi_playground/start_teleop_wheel.sh
```

기본값은 `USE_SIM_TIME=false`로, `/clock` 없이도 동작합니다.
