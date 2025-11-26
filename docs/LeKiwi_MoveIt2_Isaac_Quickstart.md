# LeKiwi MoveIt2 + Isaac Sim Quickstart

LeKiwi를 Isaac Sim과 MoveIt2로 바로 구동하기 위한 단일 가이드입니다. 설치 → 환경 변수 → Isaac 그래프 → MoveIt/RViz 실행까지 순서대로 따라가세요.

## 1) 필수 설치 (ROS Jazzy)
```bash
sudo apt update
sudo apt install -y software-properties-common curl
sudo apt install -y ros-jazzy-desktop ros-dev-tools ros-jazzy-moveit \
    python3-colcon-common-extensions python3-vcstool python3-rosdep python3-pip
sudo rosdep init || true
rosdep update
```

## 2) 워크스페이스 준비
### URDF + 메쉬 내려받기
LeKiwi URDF는 메쉬(STL)와 함께 사용해야 합니다. 깃허브 리포 전체를 클론해 `urdf/lekiwi` 디렉터리를 복사하세요.
```bash
cd ~/workspace/lerobot_ros2
git clone https://github.com/kabilankb/lekiwi_isaacsim.git /tmp/lekiwi_isaacsim
mkdir -p urdf
cp -r /tmp/lekiwi_isaacsim/urdf/lekiwi ./urdf/
```
URDF는 절대 경로로 `/home/<user>/workspace/lerobot_ros2/urdf/lekiwi/meshes/*.stl`을 바라보므로 위 위치를 그대로 유지하세요.

### 의존 설치/빌드
```bash
cd ~/workspace/lerobot_ros2
rosdep install --from-paths src --ignore-src -r -y
pip install -r requirements.txt
colcon build --symlink-install
source install/setup.bash
```

## 3) 공통 환경 변수 (Isaac/ROS 터미널 동일)
```bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=10
source /opt/ros/jazzy/setup.bash
source ~/workspace/lerobot_ros2/install/setup.bash
```

## 4) Isaac Sim 설정
1. Extensions에서 `omni.isaac.ros2_bridge` 활성화 후 Isaac 실행 (환경변수 동일 적용).
2. URDF를 `/World/LeKiwi`로 가져오기(articulation).
3. Script Editor에서 실행:
   ```python
   exec(open("/home/vpraise/workspace/lerobot_ros2/scripts/lekiwi/set_lekiwi_cameras.py").read())  # 카메라 prim (1회)
   exec(open("/home/vpraise/workspace/lerobot_ros2/scripts/lekiwi/set_omnigraph_all.py").read())  # 조인트/카메라 그래프
   ```
4. Play → `/joint_states`, 카메라 토픽이 보이는지 확인.

## 5) MoveIt2 실행
- 코어만: `./lekiwi_playground/start_moveit2_isaac.sh`
- RViz 포함: `LAUNCH_RVIZ=true ./lekiwi_playground/start_moveit2_isaac.sh`
- RViz만: `./lekiwi_playground/start_moveit2_rviz.sh`
- RViz Fixed Frame: `base_plate_layer1_v5`
- 필요 시 planning scene 브리지: `./lekiwi_playground/start_planning_scene_bridge.sh`
- 베이스 키보드 텔레옵: `./lekiwi_playground/start_base_teleop.sh` + `./lekiwi_playground/start_keyboard_teleop.sh` (자세히: [LeKiwi_Base_Teleop.md](./LeKiwi_Base_Teleop.md))

## 6) 빠른 점검
- `/joint_states` 수신: `ros2 topic echo /joint_states`
- 액션 서버: `ros2 action list | grep follow_joint_trajectory` → `/lekiwi_arm_controller/follow_joint_trajectory`
- 수동 이동:  
  `ros2 topic pub /joint_command sensor_msgs/JointState "{name: ['STS3215_03a_v1_Revolute_45'], position: [0.2]}"`
- Plan & Execute 시 `/joint_command` 퍼블리시 되는지 `ros2 topic echo /joint_command`로 확인.

## 7) 흔한 문제 / 해결
- 토픽/노드 없음 → Isaac/ROS 도메인·RMW 불일치 확인, Isaac Play 상태, `ros2 daemon stop && ros2 daemon start`.
- RViz “Frame [base_link] does not exist” → Fixed Frame을 `base_plate_layer1_v5`로 변경.
- TF 루프 의심 → PublishTF에 로봇만 지정(가능하면 targetPrims `/World/LeKiwi`), 환경 TF 비활성화 후 테스트.
- 충돌로 플랜 실패 → Start/Goal을 충돌 없는 포즈로 설정(정적 부품 충돌 완화 SRDF 포함).
- 액션 거부/순서 문제 → 최신 빌드 후 executor가 joint 순서 재정렬. 여전히 문제면 `/lekiwi_arm_controller/follow_joint_trajectory`가 뜨는지 확인.
- 실행 중단 → `/joint_command` 흐름 여부 확인, MoveIt/브리지 로그 재확인 후 스크립트 재시작.
