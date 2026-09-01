"""Dependency-free Linux joystick API to sensor_msgs/Joy publisher."""

from __future__ import annotations

import glob
import os
from pathlib import Path
import time
from typing import Optional

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy

from .core import JS_EVENT_STRUCT, ProgressHeartbeat, decode_linux_joy_event


def _matching_usb_device(
    sysfs_path: Path, vendor_id: str, product_id: str
) -> Optional[Path]:
    resolved = sysfs_path.resolve()
    for candidate in (resolved, *resolved.parents):
        vendor_file = candidate / "idVendor"
        product_file = candidate / "idProduct"
        if not vendor_file.is_file() or not product_file.is_file():
            continue
        vendor = vendor_file.read_text(encoding="ascii").strip().lower()
        product = product_file.read_text(encoding="ascii").strip().lower()
        if vendor == vendor_id.lower() and product == product_id.lower():
            return candidate
    return None


def discover_joystick(vendor_id: str, product_id: str) -> Optional[str]:
    for sysfs_name in sorted(glob.glob("/sys/class/input/js*")):
        sysfs_path = Path(sysfs_name)
        if _matching_usb_device(sysfs_path, vendor_id, product_id) is not None:
            return "/dev/input/" + sysfs_path.name
    return None


def joystick_heartbeat_path(
    device_path: str, vendor_id: str, product_id: str
) -> Optional[Path]:
    sysfs_path = Path("/sys/class/input") / Path(device_path).resolve().name
    usb_device = _matching_usb_device(sysfs_path, vendor_id, product_id)
    if usb_device is None:
        return None
    heartbeat = usb_device / "urbnum"
    return heartbeat if heartbeat.is_file() else None


class LinuxJoyNode(Node):
    def __init__(self) -> None:
        super().__init__("p0_linux_joy")
        self.declare_parameter("vendor_id", "04b4")
        self.declare_parameter("product_id", "2411")
        self.declare_parameter("device_path", "")
        self.declare_parameter("publish_period_sec", 0.05)
        self.declare_parameter("reconnect_period_sec", 1.0)
        self.declare_parameter("link_timeout_sec", 0.30)

        self._publisher = self.create_publisher(Joy, "/joy", 10)
        self._fd: Optional[int] = None
        self._device = ""
        self._heartbeat_path: Optional[Path] = None
        self._heartbeat = ProgressHeartbeat()
        self._link_alive = False
        self._link_state_reported: Optional[bool] = None
        self._buffer = bytearray()
        self._axes: list[float] = []
        self._buttons: list[int] = []
        self._last_connect_attempt = 0.0
        self.create_timer(0.01, self._read_tick)
        self.create_timer(
            float(self.get_parameter("publish_period_sec").value), self._publish_tick
        )

    def _candidate_device(self) -> Optional[str]:
        configured = str(self.get_parameter("device_path").value)
        if configured:
            return configured if os.path.exists(configured) else None
        return discover_joystick(
            str(self.get_parameter("vendor_id").value),
            str(self.get_parameter("product_id").value),
        )

    def _connect(self) -> None:
        now = time.monotonic()
        reconnect_period = float(self.get_parameter("reconnect_period_sec").value)
        if self._fd is not None or now - self._last_connect_attempt < reconnect_period:
            return
        self._last_connect_attempt = now
        candidate = self._candidate_device()
        if candidate is None:
            return
        try:
            self._fd = os.open(candidate, os.O_RDONLY | os.O_NONBLOCK)
        except OSError as exc:
            self.get_logger().warning(f"cannot open joystick {candidate}: {exc}")
            self._fd = None
            return
        self._device = candidate
        self._heartbeat_path = joystick_heartbeat_path(
            candidate,
            str(self.get_parameter("vendor_id").value),
            str(self.get_parameter("product_id").value),
        )
        self._heartbeat = ProgressHeartbeat()
        self._link_alive = False
        self._link_state_reported = None
        self._buffer.clear()
        self._axes.clear()
        self._buttons.clear()
        self.get_logger().info(f"joystick connected: {candidate}")

    def _disconnect(self, reason: str, report: bool = True) -> None:
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
        self._fd = None
        self._device = ""
        self._heartbeat_path = None
        self._heartbeat = ProgressHeartbeat()
        self._link_alive = False
        self._link_state_reported = None
        self._buffer.clear()
        self._axes.clear()
        self._buttons.clear()
        if report:
            self.get_logger().warning(f"joystick disconnected: {reason}")

    @staticmethod
    def _extend(values: list, index: int, default) -> None:
        if index >= len(values):
            values.extend([default] * (index + 1 - len(values)))

    def _read_tick(self) -> None:
        self._connect()
        if self._fd is None:
            return
        while True:
            try:
                chunk = os.read(self._fd, JS_EVENT_STRUCT.size * 64)
            except BlockingIOError:
                break
            except OSError as exc:
                self._disconnect(str(exc))
                return
            if not chunk:
                self._disconnect("end of device stream")
                return
            self._buffer.extend(chunk)
            while len(self._buffer) >= JS_EVENT_STRUCT.size:
                data = bytes(self._buffer[: JS_EVENT_STRUCT.size])
                del self._buffer[: JS_EVENT_STRUCT.size]
                event = decode_linux_joy_event(data)
                if event.kind == "axis":
                    self._extend(self._axes, event.number, 0.0)
                    self._axes[event.number] = event.value
                elif event.kind == "button":
                    self._extend(self._buttons, event.number, 0)
                    self._buttons[event.number] = int(event.value)

    def _update_link_health(self) -> bool:
        if self._heartbeat_path is None:
            self._link_alive = False
        else:
            try:
                counter = int(
                    self._heartbeat_path.read_text(encoding="ascii").strip()
                )
            except (OSError, ValueError) as exc:
                self._disconnect(f"cannot read USB heartbeat: {exc}")
                return False
            self._link_alive = self._heartbeat.observe(
                counter,
                time.monotonic(),
                float(self.get_parameter("link_timeout_sec").value),
            )

        if self._link_alive != self._link_state_reported:
            if self._link_alive:
                self.get_logger().info("joystick wireless link active")
            else:
                self.get_logger().warning(
                    "joystick wireless link unavailable; publishing neutral input"
                )
            self._link_state_reported = self._link_alive
        return self._link_alive

    def _publish_tick(self) -> None:
        if self._fd is None:
            return
        link_alive = self._update_link_health()
        message = Joy()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = self._device if link_alive else self._device + ":down"
        message.axes = list(self._axes) if link_alive else [0.0] * len(self._axes)
        message.buttons = list(self._buttons) if link_alive else [0] * len(self._buttons)
        self._publisher.publish(message)

    def destroy_node(self) -> bool:
        if self._fd is not None:
            self._disconnect("shutdown", report=False)
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = LinuxJoyNode()
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
