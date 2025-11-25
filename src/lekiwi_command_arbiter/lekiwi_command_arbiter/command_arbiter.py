#!/usr/bin/env python3
"""
LeKiwi Command Arbiter

Priority-based command arbitration for coordinated control:
- Emergency stop (priority 255)
- Teleoperation (priority 200)
- Manipulation (priority 150)
- Navigation (priority 100)
- Idle (priority 0)
"""

import rclpy
from rclpy.node import Node
from rclpy.time import Time, Duration
from geometry_msgs.msg import Twist
from sensor_msgs.msg import JointState
from control_msgs.action import FollowJointTrajectory
from std_msgs.msg import Bool, Header
import math


class CommandArbiter(Node):
    """Arbitrates commands from multiple sources based on priority"""

    # Priority levels
    PRIORITY_EMERGENCY = 255
    PRIORITY_TELEOP = 200
    PRIORITY_MANIPULATION = 150
    PRIORITY_NAVIGATION = 100
    PRIORITY_IDLE = 0

    # Command timeout (seconds)
    COMMAND_TIMEOUT = 2.0  # Increased for sim_time stability

    def __init__(self):
        super().__init__('lekiwi_command_arbiter')

        # Declare parameters
        self.declare_parameter('update_rate', 50.0)
        self.declare_parameter('command_timeout', 2.0)  # Increased timeout

        self.update_rate = self.get_parameter('update_rate').value
        self.command_timeout = self.get_parameter('command_timeout').value

        # Command storage with timestamps
        self.commands = {
            'emergency': {'cmd': None, 'time': None, 'priority': self.PRIORITY_EMERGENCY},
            'teleop': {'cmd': None, 'time': None, 'priority': self.PRIORITY_TELEOP},
            'manipulation': {'cmd': None, 'time': None, 'priority': self.PRIORITY_MANIPULATION},
            'navigation': {'cmd': None, 'time': None, 'priority': self.PRIORITY_NAVIGATION},
        }

        self.emergency_stop_active = False
        self.arm_trajectory_active = False

        # Subscribers
        self.create_subscription(Bool, '/emergency_stop', self.emergency_callback, 10)
        self.create_subscription(Twist, '/cmd_vel_teleop', self.teleop_callback, 10)
        self.create_subscription(Twist, '/cmd_vel_nav', self.navigation_callback, 10)
        self.create_subscription(JointState, '/arm_command_teleop', self.arm_teleop_callback, 10)

        # Publishers
        self.base_cmd_pub = self.create_publisher(JointState, '/base_commands', 10)
        self.arm_cmd_pub = self.create_publisher(JointState, '/arm_commands', 10)

        # Timer
        self.timer = self.create_timer(1.0 / self.update_rate, self.update_callback)

        self.get_logger().info('Command Arbiter initialized')
        self.get_logger().info(f'  Update rate: {self.update_rate} Hz')
        self.get_logger().info(f'  Command timeout: {self.command_timeout} s')

    def emergency_callback(self, msg):
        """Handle emergency stop"""
        self.emergency_stop_active = msg.data
        if self.emergency_stop_active:
            self.commands['emergency']['cmd'] = 'stop'
            self.commands['emergency']['time'] = self.get_clock().now()
            self.get_logger().warn('EMERGENCY STOP ACTIVATED')
        else:
            self.commands['emergency']['cmd'] = None
            self.get_logger().info('Emergency stop deactivated')

    def teleop_callback(self, msg):
        """Handle teleoperation velocity command"""
        self.commands['teleop']['cmd'] = msg
        self.commands['teleop']['time'] = self.get_clock().now()

    def navigation_callback(self, msg):
        """Handle navigation velocity command"""
        self.commands['navigation']['cmd'] = msg
        self.commands['navigation']['time'] = self.get_clock().now()

    def arm_teleop_callback(self, msg):
        """Handle arm teleoperation command"""
        self.commands['manipulation']['cmd'] = msg
        self.commands['manipulation']['time'] = self.get_clock().now()

    def is_command_valid(self, cmd_data):
        """Check if command is still valid (not timed out)"""
        if cmd_data['cmd'] is None:
            return False
        if cmd_data['time'] is None:
            return False

        age = (self.get_clock().now() - cmd_data['time']).nanoseconds / 1e9

        # Accept commands with negative age (future timestamps) or within timeout
        # This handles clock synchronization issues with sim_time
        if age < 0 or age < self.command_timeout:
            return True

        return False

    def get_highest_priority_command(self):
        """Get the highest priority valid command"""
        # Check commands in priority order
        for source in ['emergency', 'teleop', 'manipulation', 'navigation']:
            if self.is_command_valid(self.commands[source]):
                return source, self.commands[source]

        return 'idle', None

    def twist_to_base_command(self, twist):
        """Convert Twist to base wheel commands (kiwi drive IK)"""
        if twist is None:
            return None

        v_x = twist.linear.x
        v_y = twist.linear.y
        omega_z = twist.angular.z

        # Kiwi drive inverse kinematics
        wheel_radius = 0.055  # m
        base_radius = 0.25    # m

        # Wheel angles: 0°, 120°, 240°
        angles = [0, 2*math.pi/3, 4*math.pi/3]

        wheel_vels = []
        for theta in angles:
            v_wheel = (1/wheel_radius) * (
                -math.sin(theta) * v_x +
                 math.cos(theta) * v_y +
                 base_radius * omega_z
            )
            wheel_vels.append(v_wheel)

        # Create JointState message
        cmd = JointState()
        cmd.header = Header()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.name = [
            'ST3215_Servo_Motor_v1_2_Revolute_60',  # Wheel 1
            'ST3215_Servo_Motor_v1_1_Revolute_62',  # Wheel 2
            'ST3215_Servo_Motor_v1_Revolute_64'     # Wheel 3
        ]
        cmd.velocity = wheel_vels
        cmd.position = []  # Position control not used for base
        cmd.effort = []

        return cmd

    def update_callback(self):
        """Arbitrate and publish commands"""
        source, cmd_data = self.get_highest_priority_command()

        if source == 'emergency':
            # Emergency stop - zero all velocities
            self.publish_stop_commands()
            return

        elif source == 'idle':
            # No active commands - publish zeros
            self.publish_stop_commands()
            return

        elif source in ['teleop', 'navigation']:
            # Base velocity command
            twist = cmd_data['cmd']
            base_cmd = self.twist_to_base_command(twist)
            if base_cmd is not None:
                self.base_cmd_pub.publish(base_cmd)

        elif source == 'manipulation':
            # Arm command
            arm_cmd = cmd_data['cmd']
            if isinstance(arm_cmd, JointState):
                self.arm_cmd_pub.publish(arm_cmd)

    def publish_stop_commands(self):
        """Publish zero velocity commands"""
        # Stop base
        stop_twist = Twist()
        base_cmd = self.twist_to_base_command(stop_twist)
        if base_cmd is not None:
            self.base_cmd_pub.publish(base_cmd)

        # Stop arm (publish current positions with zero velocity)
        # This would require current state feedback
        # For now, we just don't publish arm commands


def main(args=None):
    rclpy.init(args=args)
    node = CommandArbiter()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
