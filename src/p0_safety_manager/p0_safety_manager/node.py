"""ROS 2 command arbitration node."""

from __future__ import annotations

import time

import rclpy
from p0_interfaces.msg import ChassisCmd, ChassisStatus
from p0_interfaces.srv import ClearMotionLock, StopMotion
from rclpy.node import Node

from .core import CommandArbiter, MotionInput


class SafetyManagerNode(Node):
    def __init__(self) -> None:
        super().__init__("p0_safety_manager")
        self.declare_parameter("manual_timeout_sec", 0.25)
        self.declare_parameter("autonomy_timeout_sec", 0.25)
        self.declare_parameter("manual_release_hold_sec", 0.50)
        self.declare_parameter("autonomy_enabled", False)
        self.declare_parameter("publish_period_sec", 0.05)

        self._arbiter = CommandArbiter(
            manual_timeout_sec=float(self.get_parameter("manual_timeout_sec").value),
            autonomy_timeout_sec=float(
                self.get_parameter("autonomy_timeout_sec").value
            ),
            manual_release_hold_sec=float(
                self.get_parameter("manual_release_hold_sec").value
            ),
            autonomy_enabled=bool(self.get_parameter("autonomy_enabled").value),
        )
        self._sequence = 0
        self._last_reason = ""
        self._publisher = self.create_publisher(ChassisCmd, "/p0/base/cmd_vel", 10)
        self.create_subscription(
            ChassisCmd, "/p0/manual/cmd_vel", self._on_manual, 10
        )
        self.create_subscription(
            ChassisCmd, "/p0/navigation/cmd_vel", self._on_autonomy, 10
        )
        self.create_subscription(
            ChassisStatus, "/p0/base/status", self._on_base_status, 10
        )
        self.create_service(
            StopMotion,
            "/p0/motion/stop",
            self._on_stop_motion,
        )
        self.create_service(
            ClearMotionLock,
            "/p0/motion/clear_lock",
            self._on_clear_motion_lock,
        )
        self.create_timer(
            float(self.get_parameter("publish_period_sec").value), self._tick
        )

    @staticmethod
    def _as_input(message: ChassisCmd) -> MotionInput:
        return MotionInput(
            linear_x_mps=float(message.linear_x_mps),
            angular_z_radps=float(message.angular_z_radps),
            active=bool(message.active),
            received_at=time.monotonic(),
            sequence=int(message.sequence),
        )

    def _on_manual(self, message: ChassisCmd) -> None:
        self._arbiter.update_manual(self._as_input(message))

    def _on_autonomy(self, message: ChassisCmd) -> None:
        self._arbiter.update_autonomy(self._as_input(message))

    def _on_base_status(self, message: ChassisStatus) -> None:
        self._arbiter.update_base_state(
            comm_ok=bool(message.comm_ok),
            motion_ready=bool(message.motion_ready),
        )

    def _on_stop_motion(self, request, response):
        self._arbiter.latch_motion_lock(request.reason)
        response.success = True
        response.message = "software motion lock latched"
        return response

    def _on_clear_motion_lock(self, request, response):
        del request
        self._arbiter.clear_motion_lock()
        response.success = True
        response.message = "software motion lock cleared; a new command is required"
        return response

    def _tick(self) -> None:
        result = self._arbiter.decide(time.monotonic())
        self._sequence += 1
        message = ChassisCmd()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = "base_link"
        message.linear_x_mps = result.linear_x_mps
        message.angular_z_radps = result.angular_z_radps
        message.source = result.source
        message.active = result.active
        message.sequence = self._sequence
        self._publisher.publish(message)
        if result.reason != self._last_reason:
            self.get_logger().info(f"command arbitration: {result.reason}")
            self._last_reason = result.reason


def main(args=None) -> None:
    rclpy.init(args=args)
    node = SafetyManagerNode()
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
