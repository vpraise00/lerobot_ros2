#!/usr/bin/env python3
"""
LeKiwi spin demo: publish continuously changing joint commands.

Purpose:
- Keep the Isaac Sim LeKiwi articulation moving for connection tests.
- Publishes Float64MultiArray on /joint_commands (override with --topic).

Usage:
    python scripts/lekiwi/lekiwi_spin_demo.py
    python scripts/lekiwi/lekiwi_spin_demo.py --topic /joint_commands --rate 20 --amp 0.5
"""

from __future__ import annotations

import argparse
import math

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray

DEFAULT_TOPIC = "/joint_commands"
DEFAULT_RATE = 20.0  # Hz
DEFAULT_AMP = 0.5    # normalized units


class LeKiwiSpinDemo(Node):
    """Publishes a simple periodic joint trajectory for LeKiwi."""

    def __init__(self, topic: str, rate_hz: float, amplitude: float) -> None:
        super().__init__("lekiwi_spin_demo")
        self.publisher = self.create_publisher(Float64MultiArray, topic, 10)
        self.dt = 1.0 / rate_hz
        self.amp = amplitude
        self.t = 0.0

        # Diverse frequencies per joint to create a smooth, non-static motion
        self.freqs = [1.0, 1.0, 0.8, 0.7, 1.1, 1.3, 0.5, 0.9, 1.5]

        self.get_logger().info(
            "LeKiwi spin demo started\n"
            f"  topic: {topic}\n"
            f"  rate: {rate_hz} Hz\n"
            f"  amplitude: {amplitude}"
        )

        self.create_timer(self.dt, self._tick)

    def _tick(self) -> None:
        data = [
            self.amp * math.sin(self.t * f)
            for f in self.freqs
        ]

        msg = Float64MultiArray()
        msg.data = data
        self.publisher.publish(msg)
        self.t += self.dt


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="LeKiwi spin demo publisher")
    parser.add_argument("--topic", default=DEFAULT_TOPIC, help="Output topic (Float64MultiArray)")
    parser.add_argument("--rate", type=float, default=DEFAULT_RATE, help="Publish rate in Hz")
    parser.add_argument("--amp", type=float, default=DEFAULT_AMP, help="Amplitude (normalized units)")
    args = parser.parse_args(argv)

    rclpy.init()
    node = LeKiwiSpinDemo(topic=args.topic, rate_hz=args.rate, amplitude=args.amp)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
