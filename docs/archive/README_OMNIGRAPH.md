# LeKiwi Isaac Sim Omnigraph Setup

This directory contains scripts to automate the creation and configuration of ROS2 action graphs in Isaac Sim for the LeKiwi robot.

## Quick Start

### Method 1: Run Setup Script in Isaac Sim

1. **Open Isaac Sim** and load your LeKiwi USD scene

2. **Open Script Editor** (Window → Script Editor)

3. **Run the setup script**:
   ```python
   # In Isaac Sim Python console
   import sys
   sys.path.append('/home/vpraise/workspace/lerobot_ros2/install/lekiwi_isaac_bridge/lib/python3.12/site-packages')

   from lekiwi_isaac_bridge import setup_omnigraph
   setup_omnigraph.main()
   ```

4. **Configure target prims** (manual step):
   - Open Action Graph editor (Window → Visual Scripting → Action Graph)
   - Select `ArticulationController` node
   - Set `targetPrim` to `/World/LeKiwi` (or your robot root prim path)
   - Select `PublishJointState` node
   - Set `targetPrim` to `/World/LeKiwi`

5. **Press Play** to start simulation

### Method 2: Manual Setup (if script fails)

1. **Create Action Graph**:
   - Window → Visual Scripting → Action Graph
   - Click "New Action Graph" button

2. **Add nodes** (drag from node palette):
   - `On Playback Tick`
   - `ROS2 Context`
   - `ROS2 Subscribe Joint State`
   - `Isaac Articulation Controller`
   - `ROS2 Publish Joint State`
   - `ROS2 Publish Clock`

3. **Connect nodes**:
   ```
   OnPlaybackTick.tick → SubscribeJointState.execIn
   OnPlaybackTick.tick → PublishJointState.execIn
   OnPlaybackTick.tick → PublishClock.execIn

   SubscribeJointState.jointNames → ArticulationController.jointNames
   SubscribeJointState.positionCommand → ArticulationController.positionCommand
   SubscribeJointState.velocityCommand → ArticulationController.velocityCommand
   SubscribeJointState.effortCommand → ArticulationController.effortCommand
   ```

4. **Configure node properties**:

   **ROS2 Context**:
   - `domain_id`: `10`

   **ROS2 Subscribe Joint State**:
   - `topicName`: `/joint_command`
   - `qosProfile`: `RELIABLE`

   **Isaac Articulation Controller**:
   - `targetPrim`: `/World/LeKiwi` (your robot root)

   **ROS2 Publish Joint State**:
   - `topicName`: `/joint_states`
   - `qosProfile`: `RELIABLE` (⚠️ Important: Must match subscriber)
   - `targetPrim`: `/World/LeKiwi`

   **ROS2 Publish Clock**:
   - `topicName`: `/clock`

## ROS2 Integration

### Environment Setup

Ensure your ROS2 environment is configured correctly:

```bash
export ROS_DOMAIN_ID=10
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

### Topics

| Topic | Type | QoS | Direction | Description |
|-------|------|-----|-----------|-------------|
| `/joint_command` | `sensor_msgs/JointState` | RELIABLE | ROS→Sim | Joint commands from ROS2 |
| `/joint_states` | `sensor_msgs/JointState` | RELIABLE | Sim→ROS | Joint states from Isaac Sim |
| `/clock` | `rosgraph_msgs/Clock` | DEFAULT | Sim→ROS | Simulation time |

### Testing

1. **Check topics**:
   ```bash
   ros2 topic list
   # Should show /joint_states, /joint_command, /clock
   ```

2. **Echo joint states**:
   ```bash
   ros2 topic echo /joint_states
   ```

3. **Send test command**:
   ```bash
   ros2 topic pub /joint_command sensor_msgs/JointState "
   header:
     stamp: {sec: 0, nanosec: 0}
     frame_id: ''
   name: ['ST3215_Servo_Motor_v1_2_Revolute_60', 'ST3215_Servo_Motor_v1_1_Revolute_62', 'ST3215_Servo_Motor_v1_Revolute_64']
   position: []
   velocity: [1.0, 1.0, 1.0]
   effort: []
   " --once
   ```

## Troubleshooting

### "No topics appear in ROS2"

**Cause**: QoS mismatch or domain_id mismatch

**Fix**:
1. Check `ROS_DOMAIN_ID=10` in both Isaac Sim and ROS2 terminal
2. Verify omnigraph Context node has `domain_id: 10`
3. Check QoS profiles match:
   - Isaac Sim PublishJointState: `RELIABLE`
   - ROS2 robot_state_publisher: `RELIABLE` (set via QoS overrides)

### "Joint states published but empty data"

**Cause**: `targetPrim` not set correctly

**Fix**:
1. Open Action Graph editor
2. Select `PublishJointState` node
3. Set `targetPrim` to your robot root prim path (e.g., `/World/LeKiwi`)
4. Verify path exists in Stage tree

### "Commands not reaching robot"

**Cause**: `ArticulationController` not configured

**Fix**:
1. Select `ArticulationController` node
2. Set `targetPrim` to robot root prim
3. Verify robot has physics articulation
4. Check `/joint_command` topic is publishing (use `ros2 topic echo`)

### "TF tree still empty"

**Cause**: `robot_state_publisher` not running or not receiving joint states

**Fix**:
1. Verify `/joint_states` has data: `ros2 topic echo /joint_states`
2. Check robot_state_publisher is running: `ros2 node list`
3. Verify URDF is loaded correctly
4. Check QoS compatibility (both RELIABLE)

### "Simulation time issues"

**Cause**: ROS2 nodes not using sim time

**Fix**:
1. Ensure all ROS2 nodes have `use_sim_time: true` parameter
2. Verify `/clock` is publishing: `ros2 topic echo /clock`
3. Check nodes are receiving clock: `ros2 param get <node_name> use_sim_time`

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Isaac Sim                          │
│                                                     │
│  ┌─────────────┐    /joint_states (RELIABLE)       │
│  │  LeKiwi     │───────────────────────────────────►│ ROS2
│  │  Robot      │                                    │
│  │             │    /joint_command (RELIABLE)       │
│  │             │◄───────────────────────────────────│
│  └─────────────┘                                    │
│         │                                           │
│         │                                           │
│  ┌──────▼──────────────────────────────┐           │
│  │     ROS2 Action Graph                │           │
│  │                                      │           │
│  │  ┌────────────────────────────┐     │           │
│  │  │   On Playback Tick         │     │           │
│  │  └─────┬────────┬────────┬────┘     │           │
│  │        │        │        │          │           │
│  │  ┌─────▼───┐ ┌─▼────┐ ┌─▼──────┐  │           │
│  │  │Subscribe│ │Publish│ │Publish │  │           │
│  │  │Joint    │ │Joint  │ │Clock   │  │           │
│  │  │State    │ │State  │ │        │  │           │
│  │  └────┬────┘ └───────┘ └────────┘  │           │
│  │       │                             │           │
│  │  ┌────▼──────────────────┐         │           │
│  │  │ Articulation Controller│         │           │
│  │  └────────────────────────┘         │           │
│  └──────────────────────────────────────┘          │
└─────────────────────────────────────────────────────┘

ROS2 Nodes:
- lekiwi_hardware_interface: Aggregates base/arm commands → /joint_command
- lekiwi_command_arbiter: Priority-based command arbitration
- robot_state_publisher: Publishes TF tree from /joint_states
- lekiwi_base_controller: Publishes odometry and TF (odom→base)
```

## QoS Profile Details

### Why RELIABLE?

Isaac Sim's `ROS2 Publish Joint State` node uses **RELIABLE** QoS by default. To ensure compatibility, all subscribers must also use RELIABLE:

```yaml
# ROS2 Node QoS Configuration
joint_states:
  reliability: reliable  # Must match Isaac Sim
  durability: volatile
  history: keep_last
  depth: 10
```

### Setting QoS in robot_state_publisher

```python
# In launch file:
robot_state_publisher = Node(
    package='robot_state_publisher',
    parameters=[{
        'qos_overrides./joint_states.subscription.reliability': 'reliable',
        'qos_overrides./joint_states.subscription.history': 'keep_last',
        'qos_overrides./joint_states.subscription.depth': 10,
    }],
)
```

## Files

- `setup_omnigraph.py` - Interactive setup script for Isaac Sim
- `README_OMNIGRAPH.md` - This file
- `config/lekiwi_sim.yaml` - Joint names configuration

## References

- [Isaac Sim ROS2 Bridge Documentation](https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/ext_omni_isaac_ros2_bridge.html)
- [ROS2 QoS Settings](https://docs.ros.org/en/humble/Concepts/About-Quality-of-Service-Settings.html)
- [Omniverse Action Graph](https://docs.omniverse.nvidia.com/extensions/latest/ext_omnigraph.html)
