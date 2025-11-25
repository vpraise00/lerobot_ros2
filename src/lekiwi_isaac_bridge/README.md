# lekiwi_isaac_bridge

ROS2 sidecar node to convert `/joint_commands` (Float64MultiArray) into `/joint_command` (JointState) for the LeKiwi articulation in Isaac Sim.

## Usage

```bash
colcon build --packages-select lekiwi_isaac_bridge
source install/setup.bash
ros2 run lekiwi_isaac_bridge bridge_node
```

Default topics and joint names are loaded from `config/lekiwi_sim.yaml`.

Isaac Sim side:
- Action Graph already publishes `/joint_states` and subscribes to `/joint_command` (JointState) bound to `/World/LeKiwi`.
- When this bridge runs, any `/joint_commands` published by `lerobot_ros2` will be forwarded as `/joint_command` with the configured joint order.

Launch alternative:
```bash
ros2 launch lekiwi_isaac_bridge lekiwi_isaac_bridge.launch.py
```

Adjust parameters:
- `config` (path to YAML)
- `input_topic` (default `/joint_commands`)
- `output_topic` (default `/joint_command`)
