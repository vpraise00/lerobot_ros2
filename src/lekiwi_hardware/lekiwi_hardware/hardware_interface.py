#!/usr/bin/env python3
"""
LeKiwi Hardware Interface

Bridges Isaac Sim with ROS2 controllers:
- Reads /joint_states from Isaac Sim
- Writes /base_commands and /arm_commands to Isaac Sim
- Provides state estimation and command aggregation
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from sensor_msgs.msg import JointState
from std_msgs.msg import Header


class LeKiwiHardwareInterface(Node):
    """Hardware interface for LeKiwi robot in Isaac Sim"""

    # Joint name constants
    BASE_JOINTS = [
        'ST3215_Servo_Motor_v1_2_Revolute_60',  # Wheel 1 (0°)
        'ST3215_Servo_Motor_v1_1_Revolute_62',  # Wheel 2 (120°)
        'ST3215_Servo_Motor_v1_Revolute_64'     # Wheel 3 (240°)
    ]

    ARM_JOINTS = [
        'STS3215_03a_v1_Revolute_45',           # Shoulder base
        'STS3215_03a_v1_1_Revolute_49',         # Shoulder tilt
        'STS3215_03a_v1_2_Revolute_51',         # Elbow
        'STS3215_03a_v1_3_Revolute_53',         # Wrist roll 1
        'STS3215_03a_Wrist_Roll_v1_Revolute_55',# Wrist roll 2
        'STS3215_03a_v1_4_Revolute_57'          # End effector pitch
    ]

    def __init__(self):
        super().__init__('lekiwi_hardware_interface')

        # Declare parameters
        self.declare_parameter('update_rate', 50.0)

        # Get update rate
        self.update_rate = self.get_parameter('update_rate').value

        # Load QoS profiles (try to import, fallback to default if not available)
        try:
            import sys
            sys.path.append('/home/vpraise/workspace/lerobot_ros2/install/lekiwi_core/lib/python3/dist-packages')
            from lekiwi_core.qos import get_qos_profile
            joint_states_qos = get_qos_profile('joint_states')
            commands_qos = get_qos_profile('joint_commands')
        except Exception as e:
            self.get_logger().warn(f'Could not load lekiwi_core QoS: {e}, using default')
            joint_states_qos = 10
            commands_qos = 10

        # State storage
        self.latest_joint_states = None
        self.base_command = None
        self.arm_command = None

        # Subscribe to Isaac Sim joint states
        self.joint_state_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            joint_states_qos
        )

        # Subscribe to command topics
        self.base_cmd_sub = self.create_subscription(
            JointState,
            '/base_commands',
            self.base_command_callback,
            commands_qos
        )

        self.arm_cmd_sub = self.create_subscription(
            JointState,
            '/arm_commands',
            self.arm_command_callback,
            commands_qos
        )

        # Publish aggregated commands to Isaac Sim
        self.joint_cmd_pub = self.create_publisher(
            JointState,
            '/joint_command',
            commands_qos
        )

        # Update timer
        self.timer = self.create_timer(
            1.0 / self.update_rate,
            self.update_callback
        )

        self.get_logger().info('LeKiwi Hardware Interface initialized')
        self.get_logger().info(f'  Update rate: {self.update_rate} Hz')
        self.get_logger().info(f'  Base joints: {len(self.BASE_JOINTS)}')
        self.get_logger().info(f'  Arm joints: {len(self.ARM_JOINTS)}')

    def joint_state_callback(self, msg):
        """Store latest joint states from Isaac Sim"""
        self.latest_joint_states = msg

    def base_command_callback(self, msg):
        """Store latest base command"""
        self.base_command = msg

    def arm_command_callback(self, msg):
        """Store latest arm command"""
        self.arm_command = msg

    def update_callback(self):
        """Aggregate and publish commands"""
        if self.base_command is None and self.arm_command is None:
            return  # No commands to send

        # Create aggregated command message
        cmd = JointState()
        cmd.header = Header()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.header.frame_id = ''

        cmd.name = []
        cmd.position = []
        cmd.velocity = []
        cmd.effort = []

        # Add base commands
        if self.base_command is not None:
            for i, joint_name in enumerate(self.base_command.name):
                if joint_name in self.BASE_JOINTS:
                    cmd.name.append(joint_name)
                    if len(self.base_command.position) > i:
                        cmd.position.append(self.base_command.position[i])
                    if len(self.base_command.velocity) > i:
                        cmd.velocity.append(self.base_command.velocity[i])
                    if len(self.base_command.effort) > i:
                        cmd.effort.append(self.base_command.effort[i])

        # Add arm commands
        if self.arm_command is not None:
            for i, joint_name in enumerate(self.arm_command.name):
                if joint_name in self.ARM_JOINTS:
                    cmd.name.append(joint_name)
                    if len(self.arm_command.position) > i:
                        cmd.position.append(self.arm_command.position[i])
                    if len(self.arm_command.velocity) > i:
                        cmd.velocity.append(self.arm_command.velocity[i])
                    if len(self.arm_command.effort) > i:
                        cmd.effort.append(self.arm_command.effort[i])

        # Publish aggregated command
        if len(cmd.name) > 0:
            self.joint_cmd_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = LeKiwiHardwareInterface()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
