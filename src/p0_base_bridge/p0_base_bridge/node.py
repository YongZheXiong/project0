"""Fail-safe ROS 2 bridge for the Project0 H60 binary protocol."""

from __future__ import annotations

import queue
import threading
import time
from typing import Optional

import rclpy
from p0_interfaces.msg import ChassisCmd, ChassisStatus
from rclpy.node import Node

from .h60_protocol import (
    H60CommandPlanner,
    MSG_ACK,
    MSG_DISARM,
    MSG_NACK,
    MSG_STOP,
    MSG_TELEMETRY,
    MotionGate,
    MotionIntent,
    Packet,
    PacketParser,
    STATUS_NAMES,
    differential_targets_mmps,
    encode_packet,
)
from .serial_port import PosixSerialPort


class BaseBridgeNode(Node):
    def __init__(self) -> None:
        super().__init__("p0_base_bridge")
        self.declare_parameter("serial_device", "/dev/ttyTHS1")
        self.declare_parameter("baud_rate", 115200)
        self.declare_parameter("command_timeout_sec", 0.20)
        self.declare_parameter("comm_timeout_sec", 0.35)
        self.declare_parameter("refresh_period_sec", 0.05)
        self.declare_parameter("heartbeat_period_sec", 0.10)
        self.declare_parameter("linear_deadband_mps", 0.01)
        self.declare_parameter("angular_deadband_radps", 0.02)
        self.declare_parameter("motion_commands_enabled", False)
        self.declare_parameter("wheel_mapping_confirmed", False)
        self.declare_parameter("track_width_m", 0.18416)
        self.declare_parameter("wheel_target_limit_mmps", 0)
        self.declare_parameter(
            "channel_wheels",
            ["unmapped_a", "unmapped_b", "unmapped_c", "unmapped_d"],
        )
        self.declare_parameter("channel_signs", [1, 1, 1, 1])

        heartbeat_ms = int(
            round(float(self.get_parameter("heartbeat_period_sec").value) * 1000.0)
        )
        self._planner = H60CommandPlanner(
            heartbeat_period_ms=heartbeat_ms,
            linear_deadband_mps=float(
                self.get_parameter("linear_deadband_mps").value
            ),
            angular_deadband_radps=float(
                self.get_parameter("angular_deadband_radps").value
            ),
        )
        self._parser = PacketParser()
        self._comm_timeout_sec = float(self.get_parameter("comm_timeout_sec").value)
        if self._comm_timeout_sec <= 0.0:
            raise ValueError("comm_timeout_sec must be positive")

        self._serial: Optional[PosixSerialPort] = None
        self._serial_lock = threading.Lock()
        self._stop_reader = threading.Event()
        self._reader: Optional[threading.Thread] = None
        self._rx_queue: queue.SimpleQueue[Optional[bytes]] = queue.SimpleQueue()
        self._last_connect_attempt = 0.0
        self._last_rx_time = 0.0
        self._last_cmd_time = 0.0
        self._latest_cmd: Optional[ChassisCmd] = None
        self._last_event = "startup"

        self._status_pub = self.create_publisher(ChassisStatus, "/p0/base/status", 10)
        self.create_subscription(ChassisCmd, "/p0/base/cmd_vel", self._on_command, 10)
        self.create_timer(
            float(self.get_parameter("refresh_period_sec").value),
            self._control_tick,
        )
        self.create_timer(0.01, self._receive_tick)
        self.create_timer(0.10, self._publish_status)

    def _on_command(self, message: ChassisCmd) -> None:
        self._latest_cmd = message
        self._last_cmd_time = time.monotonic()

    def _connect(self) -> None:
        now = time.monotonic()
        if (
            self._serial is not None
            or (self._reader is not None and self._reader.is_alive())
            or now - self._last_connect_attempt < 1.0
        ):
            return
        self._last_connect_attempt = now
        try:
            handle = PosixSerialPort(
                str(self.get_parameter("serial_device").value),
                int(self.get_parameter("baud_rate").value),
            )
        except (OSError, ValueError) as exc:
            self._last_event = f"serial_open_failed:{exc}"
            return
        self._serial = handle
        self._parser.reset()
        self._planner.reset()
        self._last_rx_time = 0.0
        while True:
            try:
                self._rx_queue.get_nowait()
            except queue.Empty:
                break
        self._stop_reader.clear()
        self._reader = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader.start()
        self._last_event = "serial_connected"

    def _disconnect(self, reason: str) -> None:
        self._last_event = reason
        self._stop_reader.set()
        reader = self._reader
        self._reader = None
        with self._serial_lock:
            handle = self._serial
            self._serial = None
            if handle is not None:
                try:
                    handle.close()
                except OSError:
                    pass
        if reader is not None and reader.is_alive():
            reader.join(timeout=0.2)
            if reader.is_alive():
                self._reader = reader
        self._planner.reset()
        self._last_rx_time = 0.0

    def _reader_loop(self) -> None:
        while not self._stop_reader.is_set():
            with self._serial_lock:
                handle = self._serial
            if handle is None:
                return
            try:
                raw = handle.read(512, 0.05)
            except OSError:
                self._rx_queue.put(None)
                return
            if raw:
                self._rx_queue.put(raw)

    def _write_packet(self, packet: Packet) -> bool:
        payload = encode_packet(packet)
        with self._serial_lock:
            handle = self._serial
            if handle is None:
                return False
            try:
                handle.write(payload)
            except (OSError, TimeoutError):
                return False
        return True

    def _gate(self) -> MotionGate:
        return MotionGate(
            motion_commands_enabled=bool(
                self.get_parameter("motion_commands_enabled").value
            ),
            wheel_mapping_confirmed=bool(
                self.get_parameter("wheel_mapping_confirmed").value
            ),
        )

    def _motion_configuration_valid(self) -> bool:
        try:
            differential_targets_mmps(
                0.0,
                0.0,
                float(self.get_parameter("track_width_m").value),
                list(self.get_parameter("channel_wheels").value),
                [int(value) for value in self.get_parameter("channel_signs").value],
                int(self.get_parameter("wheel_target_limit_mmps").value),
            )
        except (TypeError, ValueError):
            return False
        return True

    def _control_tick(self) -> None:
        self._connect()
        if self._serial is None:
            return

        now = time.monotonic()
        timeout = float(self.get_parameter("command_timeout_sec").value)
        command_fresh = (
            self._latest_cmd is not None
            and self._last_cmd_time > 0.0
            and 0.0 <= now - self._last_cmd_time <= timeout
        )
        if self._latest_cmd is None:
            intent = MotionIntent(0.0, 0.0, False)
        else:
            intent = MotionIntent(
                float(self._latest_cmd.linear_x_mps),
                float(self._latest_cmd.angular_z_radps),
                bool(self._latest_cmd.active),
            )

        try:
            planned = self._planner.plan(
                now_ms=int(now * 1000.0),
                intent=intent,
                command_fresh=command_fresh,
                gate=self._gate(),
                track_width_m=float(self.get_parameter("track_width_m").value),
                channel_wheels=list(self.get_parameter("channel_wheels").value),
                channel_signs=[
                    int(value) for value in self.get_parameter("channel_signs").value
                ],
                wheel_target_limit_mmps=int(
                    self.get_parameter("wheel_target_limit_mmps").value
                ),
            )
        except (OverflowError, ValueError) as exc:
            self._last_event = f"command_plan_failed:{exc}"
            if not self._write_packet(Packet(MSG_STOP)):
                self._disconnect("serial_stop_failed")
            return

        if planned.reason != self._last_event and planned.reason not in {
            "idle",
            "idle_heartbeat",
            "armed_heartbeat",
        }:
            self._last_event = planned.reason
        if planned.packet is not None and not self._write_packet(planned.packet):
            self._disconnect("serial_write_failed")

    def _receive_tick(self) -> None:
        while True:
            try:
                raw = self._rx_queue.get_nowait()
            except queue.Empty:
                return
            if raw is None:
                self._disconnect("serial_read_failed")
                return
            for packet in self._parser.feed(raw):
                if packet.message_type not in (MSG_TELEMETRY, MSG_ACK, MSG_NACK):
                    self._last_event = f"unexpected_packet_type:0x{packet.message_type:02x}"
                    continue
                try:
                    self._planner.observe(packet)
                except ValueError as exc:
                    self._last_event = f"invalid_h60_payload:{exc}"
                    continue
                self._last_rx_time = time.monotonic()
                if packet.message_type in (MSG_ACK, MSG_NACK):
                    response = self._planner.last_response
                    if response is not None:
                        prefix = "nack" if response.nack else "ack"
                        self._last_event = (
                            f"{prefix}:cmd=0x{response.command_type:02x}:"
                            f"{STATUS_NAMES.get(response.status, response.status)}"
                        )

    def _publish_status(self) -> None:
        now = time.monotonic()
        age = now - self._last_rx_time if self._last_rx_time > 0.0 else float("inf")
        telemetry = self._planner.telemetry
        response = self._planner.last_response
        comm_ok = self._serial is not None and age < self._comm_timeout_sec
        gate = self._gate()
        motion_ready = bool(
            comm_ok
            and gate.motion_commands_enabled
            and gate.wheel_mapping_confirmed
            and self._motion_configuration_valid()
            and self._planner.device_motion_ready
        )

        message = ChassisStatus()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = "base_link"
        message.comm_ok = comm_ok
        message.motion_ready = motion_ready
        message.armed = self._planner.armed
        message.fault_latched = bool(telemetry and telemetry.fault_latched)
        message.self_test_ok = bool(telemetry and telemetry.self_test_ok)
        message.motion_output_available = bool(
            telemetry and telemetry.motion_output_available
        )
        message.protocol_version = 1
        message.session_id = telemetry.session_id if telemetry else 0
        message.telemetry_sequence = telemetry.sequence if telemetry else 0
        message.h60_state = telemetry.state if telemetry else 0
        message.h60_fault = telemetry.fault if telemetry else 0
        message.firmware_major = telemetry.firmware_version[0] if telemetry else 0
        message.firmware_minor = telemetry.firmware_version[1] if telemetry else 0
        message.firmware_patch = telemetry.firmware_version[2] if telemetry else 0
        message.raw_encoder_a = telemetry.encoder_count[0] if telemetry else 0
        message.raw_encoder_b = telemetry.encoder_count[1] if telemetry else 0
        message.raw_encoder_c = telemetry.encoder_count[2] if telemetry else 0
        message.raw_encoder_d = telemetry.encoder_count[3] if telemetry else 0
        message.encoder_delta_a = telemetry.encoder_delta[0] if telemetry else 0
        message.encoder_delta_b = telemetry.encoder_delta[1] if telemetry else 0
        message.encoder_delta_c = telemetry.encoder_delta[2] if telemetry else 0
        message.encoder_delta_d = telemetry.encoder_delta[3] if telemetry else 0
        message.vin_adc_raw = telemetry.vin_raw if telemetry else 0
        message.vin_nominal_mv = telemetry.vin_nominal_mv if telemetry else 0
        message.boot_fault_code = telemetry.boot_fault_code if telemetry else 0
        message.last_response_command = response.command_type if response else 0
        message.last_response_status = response.status if response else 0
        message.last_response_nack = bool(response and response.nack)
        message.protocol_error_count = (
            self._parser.stats.length_errors
            + self._parser.stats.version_errors
            + self._parser.stats.crc_errors
        )

        # Legacy wheel fields stay neutral until H6 freezes A-D mapping,
        # direction, CPR and wheel geometry. They must not carry guessed data.
        message.estop_active = False
        message.control_state = telemetry.state_name if telemetry else "UNKNOWN"
        message.motion_mode = "ARMED" if self._planner.armed else "STOP"
        message.compare = 0
        message.raw_encoder_lf = 0
        message.raw_encoder_lr = 0
        message.raw_encoder_rf = 0
        message.raw_encoder_rr = 0
        message.encoder_lf = 0
        message.encoder_lr = 0
        message.encoder_rf = 0
        message.encoder_rr = 0
        message.encoder_calibrated = False
        message.wheel_revolutions_lf = 0.0
        message.wheel_revolutions_lr = 0.0
        message.wheel_revolutions_rf = 0.0
        message.wheel_revolutions_rr = 0.0
        message.rx_age_sec = min(age, 3.4e38)
        message.last_event = self._last_event
        self._status_pub.publish(message)

    def destroy_node(self) -> bool:
        if self._serial is not None:
            self._write_packet(Packet(MSG_STOP))
            self._write_packet(Packet(MSG_DISARM))
        self._disconnect("shutdown")
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = BaseBridgeNode()
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
