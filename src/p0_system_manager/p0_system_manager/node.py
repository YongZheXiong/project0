"""系统模式状态/请求入口，默认待机；状态发布本身不ARM。"""
import time
import uuid

import rclpy
from rclpy.node import Node
from p0_interfaces.msg import ChassisCmd, ChassisStatus, SystemStatus
from p0_interfaces.srv import SetSystemMode

from .core import BaseState, ManualState, SystemModeManager


class SystemManagerNode(Node):
    def __init__(self):
        super().__init__('p0_system_manager')
        self.declare_parameter('base_timeout_sec', .35)
        self.declare_parameter('manual_timeout_sec', .25)
        self.declare_parameter('publish_period_sec', .05)
        self._manager = SystemModeManager(epoch=uuid.uuid4().hex,
            base_timeout_sec=float(self.get_parameter('base_timeout_sec').value),
            manual_timeout_sec=float(self.get_parameter('manual_timeout_sec').value))
        # depth=1、默认RELIABLE/VOLATILE；不为迟到订阅者重放旧许可。
        self._publisher = self.create_publisher(SystemStatus, '/p0/system/status', 1)
        self.create_subscription(ChassisStatus, '/p0/base/status', self._on_base, 1)
        self.create_subscription(ChassisCmd, '/p0/manual/cmd_vel', self._on_manual, 1)
        self.create_service(SetSystemMode, '/p0/system/set_mode', self._on_mode)
        self.create_timer(float(self.get_parameter('publish_period_sec').value), self._publish)

    def _on_base(self, message):
        self._manager.update_base(BaseState(bool(message.comm_ok), bool(message.motion_ready),
            bool(message.fault_latched), time.monotonic()))
        self._publish()

    def _on_manual(self, message):
        self._manager.update_manual(ManualState(bool(message.active), float(message.linear_x_mps),
            float(message.angular_z_radps), time.monotonic()))

    def _on_mode(self, request, response):
        response.success, response.message = self._manager.request_mode(request.target_mode, time.monotonic())
        response.current_mode = self._manager.mode
        self._publish()
        return response

    def _publish(self):
        state = self._manager.evaluate(time.monotonic())
        message = SystemStatus()
        message.header.stamp = self.get_clock().now().to_msg()
        for key in state.__dataclass_fields__:
            setattr(message, key, getattr(state, key))
        self._publisher.publish(message)


def main(args=None):
    rclpy.init(args=args)
    node = SystemManagerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            try:
                node.destroy_node()
            except KeyboardInterrupt:
                pass
        finally:
            if rclpy.ok(): rclpy.shutdown()
