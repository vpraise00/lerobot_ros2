# LeKiwi Base Keyboard Teleop (Isaac Sim)

LeKiwi 3륜 베이스를 키보드로 움직이는 최소 절차입니다. MoveIt/arbiter 없이 `/cmd_vel`을 바로 `/joint_command`로 변환합니다.

## 준비
- Isaac Sim: `set_lekiwi_cameras.py`(1회) 후 `set_omnigraph_all.py` 실행, Play 상태
- `ROS_DOMAIN_ID` Isaac과 동일
- 패키지: `sudo apt install ros-jazzy-teleop-twist-keyboard` (없으면 한 번 설치)
- 워크스페이스 빌드 완료: `source install/setup.bash`

## 실행 (두 터미널 사용)
1. 터미널 A: 베이스 컨트롤러 기동 (`/cmd_vel` → `/joint_command`, odom/TF 발행)
   ```bash
   ./lekiwi_playground/start_base_teleop.sh  # 기본 USE_SIM_TIME=false (Isaac /clock 없이도 동작)
   ```
   - 이 터미널에서는 키 입력을 받아도 동작하지 않습니다. 단순히 컨트롤러 로그만 보여줍니다.
2. 터미널 B: 키보드 텔레옵 실행(`/cmd_vel` 퍼블리시)
   ```bash
   ./lekiwi_playground/start_keyboard_teleop.sh
   # 또는 직접 실행:
   # ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel
   ```
   - 기본 키: i/k(전후), j/l(좌우), u/o(회전 포함), 스페이스/.(정지/감속)

## 확인
- Isaac → ROS `/joint_states`가 오는지: `ros2 topic echo /joint_states`
- `/joint_command`에 베이스 조인트 3개가 퍼블리시되는지: `ros2 topic echo /joint_command`
- odom/TF: `ros2 topic echo /odom` 또는 `ros2 run tf2_tools view_frames`

## 참고/트러블슈팅
- MoveIt/arbiter 등 다른 노드가 동시에 `/joint_command`를 퍼블리시하면 충돌 가능하니 텔레옵만 돌릴 때는 끄는 걸 권장합니다.
- 움직임이 없으면 `ROS_DOMAIN_ID`, Isaac Play 상태, `/joint_states` 스트림을 우선 확인하세요.
- Isaac이 `/clock`을 안 보낼 때는 `USE_SIM_TIME=false`가 안전합니다(기본). Isaac `/clock`을 쓰고 싶으면 `USE_SIM_TIME=true ./lekiwi_playground/start_base_teleop.sh`.
