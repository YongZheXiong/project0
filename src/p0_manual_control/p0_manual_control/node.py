"""ROS 2 Joy to Project0 manual command adapter."""

from __future__ import annotations

import time

import rclpy
from p0_interfaces.msg import ChassisCmd
from rclpy.node import Node
from sensor_msgs.msg import Joy

from .core import JoyMapping, ManualIntent, map_joy


class ManualControlNode(Node):
    def __init__(self) -> None:
        super().__init__("p0_manual_control")
        self.declare_parameter("mapping_confirmed", False)
        self.declare_parameter("linear_axis", -1)
        self.declare_parameter("angular_axis", -1)
        self.declare_parameter("deadman_button", -1)
        self.declare_parameter("linear_scale", 0.20)
        self.declare_parameter("angular_scale", 0.80)
        self.declare_parameter("deadzone", 0.10)
        self.declare_parameter("joy_timeout_sec", 0.25)
        self.declare_parameter("publish_period_sec", 0.05)

        self._publisher = self.create_publisher(ChassisCmd, "/p0/manual/cmd_vel", 10)
        self.create_subscription(Joy, "/joy", self._on_joy, 10)
        self.create_timer(
            float(self.get_parameter("publish_period_sec").value), self._tick
        )
        self._latest = ManualIntent(0.0, 0.0, False, "no_joy")
        self._last_joy_time = 0.0
        self._sequence = 0
        self._last_reason = ""

    def _mapping(self) -> JoyMapping:
        return JoyMapping(
            mapping_confirmed=bool(self.get_parameter("mapping_confirmed").value),
            linear_axis=int(self.get_parameter("linear_axis").value),
            angular_axis=int(self.get_parameter("angular_axis").value),
            deadman_button=int(self.get_parameter("deadman_button").value),
            linear_scale=float(self.get_parameter("linear_scale").value),
            angular_scale=float(self.get_parameter("angular_scale").value),
            deadzone=float(self.get_parameter("deadzone").value),
        )

    def _on_joy(self, message: Joy) -> None:
        self._latest = map_joy(message.axes, message.buttons, self._mapping())
        self._last_joy_time = time.monotonic()

    def _tick(self) -> None:
        age = time.monotonic() - self._last_joy_time
        timeout = float(self.get_parameter("joy_timeout_sec").value)
        if self._last_joy_time <= 0.0 or age > timeout:
            intent = ManualIntent(0.0, 0.0, False, "joy_timeout")
        else:
            intent = self._latest

        self._sequence += 1
        message = ChassisCmd()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = "base_link"
        message.linear_x_mps = intent.linear_x_mps
        message.angular_z_radps = intent.angular_z_radps
        message.source = "manual"
        message.active = intent.active
        message.sequence = self._sequence
        self._publisher.publish(message)
        if intent.reason != self._last_reason:
            self.get_logger().info(f"manual input: {intent.reason}")
            self._last_reason = intent.reason


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ManualControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.destroy_node()
        except KeyboardInterrupt:
            pass
        if rclpy.ok():
            rclpy.shutdown()
