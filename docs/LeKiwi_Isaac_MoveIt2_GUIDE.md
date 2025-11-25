# LeKiwi + Isaac Sim + MoveIt2 Quick Guide

This guide documents how to drive the LeKiwi arm in Isaac Sim using MoveIt2 and the existing FollowJointTrajectory bridge. The OmniGraph scripts were adjusted so JointState publishing targets the articulation root prim (`/World/LeKiwi`) for reliable joint discovery.

## Prerequisites
- Isaac Sim with ROS2 bridge extensions enabled (Domain ID matches ROS2).
- LeKiwi URDF imported as an articulation under `/World/LeKiwi` (keep joint names from `urdf/lekiwi/lekiwi.urdf`).
- ROS2 environment sourced; this workspace built and sourced.

## Isaac Sim: Create the Action Graph
1. Import the URDF (File → Import → URDF) and verify the articulation root prim path: `/World/LeKiwi`. If different, edit the constants in the scripts below.
2. (한 번만) 카메라 prim 생성: Isaac **Script Editor**에서
   ```python
   exec(open("/home/vpraise/workspace/lerobot_ros2/scripts/lekiwi/set_lekiwi_cameras.py").read())
   ```
   - 데코용 mesh 아래에 `Camera` prim을 붙입니다. 여러 번 실행해도 중복 생성되지 않습니다.
3. 단일 Action Graph(조인트 + 카메라) 구성:
   ```python
   import omni.graph.core as og
   gp="/World/LeKiwi/ActionGraph"
   if og.Controller.is_graph_path(gp):
       og.Controller.delete_graph(gp)  # 기존 그래프가 있다면 삭제
   exec(open("/home/vpraise/workspace/lerobot_ros2/scripts/lekiwi/set_omnigraph_all.py").read())
   ```
   - 단일 그래프 안에 조인트/카메라 노드가 함께 생성됩니다.
   - `/joint_command`(JointState) → `IsaacArticulationController`, `/joint_states` 퍼블리시, `/tf` 퍼블리시.
   - 카메라 2개 RenderProduct →  
     - `/lekiwi/camera/base/image_raw` (frame_id `lekiwi_camera_base_optical_frame`, anchor: 몸체 카메라 `Camera_Model_v3`)  
     - `/lekiwi/camera/wrist/image_raw` (frame_id `lekiwi_camera_wrist_optical_frame`, anchor: 팔/손목 카메라 `Camera_Model_v3_1`)
   - 시간은 기본적으로 SystemTime을 사용해 ROS 노드와 시각을 맞춥니다. (시뮬레이션 시간으로 쓰고 싶다면 `IsaacReadSimulationTime`으로 교체하고 ROS 쪽을 `use_sim_time:=true`로 실행.)
4. Press **Play** so the graphs tick. Confirm `/joint_states` and camera topics are being published (see ROS2 side below).

## ROS2: Launch MoveIt2 with the bridge
Run MoveIt + trajectory executor (FollowJointTrajectory → `/joint_command`):
- MoveIt 코어만 실행 (RViz 분리):
  ```bash
  USE_SIM_TIME=false ./lekiwi_playground/start_moveit2_isaac.sh   # RViz 미실행, 코어만
  ```
- RViz만 별도로 실행 (코어 실행 후):
  ```bash
  USE_SIM_TIME=false ./lekiwi_playground/start_moveit2_rviz.sh
  ```
- 둘을 한 번에 띄우고 싶다면:
  ```bash
  USE_SIM_TIME=false LAUNCH_RVIZ=true ./lekiwi_playground/start_moveit2_isaac.sh
  ```
- (옵션) RViz에서 planning scene을 못 받을 때: planning scene QoS 브리지 실행
  ```bash
  lekiwi_playground/start_planning_scene_bridge.sh
  ```
  - `/monitored_planning_scene`를 volatile → transient_local로 재퍼블리시하여 RViz가 초기 씬을 받을 수 있게 합니다.
- 직접 실행 예시
  ```bash
  ros2 launch lekiwi_moveit2 moveit_with_executor.launch.py use_sim_time:=false launch_rviz:=false
  ros2 launch lekiwi_moveit2 rviz_only.launch.py use_sim_time:=false
  ```
- 포함 노드:
  - MoveIt `move_group` with `robot_description` from `lekiwi.urdf`.
  - RViz(선택적으로 별도).
  - `lekiwi_arm_trajectory_executor` (action: `/lekiwi_arm_controller/follow_joint_trajectory`, output: `/joint_command`).

## End-to-end flow
1. Start Isaac Sim (with Domain ID set) and import LeKiwi.
2. Run the OmniGraph script above and press Play.
3. In another terminal, source ROS2 + workspace and run the MoveIt launch command.
4. Plan and execute in RViz; trajectories are sent over FollowJointTrajectory → `/joint_command` → Isaac Articulation → `/joint_states` → MoveIt feedback.

## Quick sanity checks
- Verify topics:
  ```bash
  ros2 topic list | grep joint
  ```
- Ensure Isaac publishes joint states:
  ```bash
  ros2 topic echo /joint_states
  ```
- Manual poke (should move in sim):
  ```bash
  ros2 topic pub /joint_command sensor_msgs/JointState "{name: ['STS3215_03a_v1_Revolute_45'], position: [0.2]}"
  ```

### RViz 고정 프레임 주의
- LeKiwi URDF의 루트 링크는 `base_plate_layer1_v5`입니다. RViz Global Options의 Fixed Frame을 `base_plate_layer1_v5`로 설정하세요. 기본값 `base_link`로 두면 “Frame [base_link] does not exist” 에러가 뜹니다.
- 만약 `base_link` 이름이 꼭 필요하면 임시 정적 TF로 매핑할 수 있습니다:
  ```bash
  ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 base_plate_layer1_v5 base_link
  ```
  (권장: Fixed Frame만 올바르게 바꾸는 방법)

## If something is off
- Planning scene를 RViz가 못 받을 때:
  - `start_planning_scene_bridge.sh`로 QoS 브리지 실행 후,
  - RViz MotionPlanning 디스플레이에서 Planning Scene Topic을 `/monitored_planning_scene`로 설정, QoS를 Reliable + Transient Local로 맞추기.
- RViz가 너무 먼저 떠서 씬 요청이 실패하는 경우: 코어와 RViz를 분리 실행(위 스크립트).
- Joint names must match URDF; check the imported articulation joint list.
- If your prim path is not `/World/LeKiwi`, edit `TARGET_ARTICULATION` / `TARGET_ROOT_PRIM` in `scripts/lekiwi/set_omnigraph_jointstate.py`.
- Make sure Isaac is in Play mode and ROS2 bridge extensions are enabled.
- Domain ID/RMW mismatch will block communication—align them before launching Isaac.
