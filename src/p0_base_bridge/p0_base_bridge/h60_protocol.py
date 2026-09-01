"""ROS-independent OpenCTR H60 binary protocol and safe session planner."""

from __future__ import annotations

from dataclasses import dataclass
import math
import secrets
import struct
import zlib
from typing import Callable, Optional, Sequence, Tuple


SOF = b"\xA5\x5A"
PROTOCOL_VERSION = 1
MAX_PAYLOAD = 48
HEADER_BYTES = 14
FIXED_BYTES = 18
MAX_FRAME = FIXED_BYTES + MAX_PAYLOAD

MSG_HEARTBEAT = 0x01
MSG_ARM = 0x02
MSG_DISARM = 0x03
MSG_STOP = 0x04
MSG_WHEEL_TARGET = 0x05
MSG_CLEAR_FAULT = 0x06
MSG_TELEMETRY = 0x80
MSG_ACK = 0x81
MSG_NACK = 0x82

STATE_BOOT = 0
STATE_DISARMED = 1
STATE_ARMED = 2
STATE_FAULT = 3

STATUS_OK = 0
STATUS_MOTION_LOCKED = 8

STATE_NAMES = {
    STATE_BOOT: "BOOT",
    STATE_DISARMED: "DISARMED",
    STATE_ARMED: "ARMED",
    STATE_FAULT: "FAULT",
}
FAULT_NAMES = {
    0: "NONE",
    1: "SELF_TEST",
    2: "PROTOCOL",
    3: "SEQUENCE",
    4: "SESSION",
    5: "TIMEOUT",
    6: "LOCAL",
    7: "WATCHDOG_PRETRIP",
}
STATUS_NAMES = {
    0: "OK",
    1: "BAD_STATE",
    2: "SELF_TEST_REQUIRED",
    3: "HEARTBEAT_REQUIRED",
    4: "BAD_SESSION",
    5: "BAD_SEQUENCE",
    6: "BAD_PAYLOAD",
    7: "UNKNOWN_COMMAND",
    8: "MOTION_LOCKED",
    9: "FAULT_LATCHED",
}


@dataclass(frozen=True)
class Packet:
    message_type: int
    session_id: int = 0
    sequence: int = 0
    payload: bytes = b""


@dataclass(frozen=True)
class Telemetry:
    state: int
    fault: int
    motion_output_available: bool
    self_test_ok: bool
    encoder_count: Tuple[int, int, int, int]
    encoder_delta: Tuple[int, int, int, int]
    vin_raw: int
    vin_nominal_mv: int
    firmware_version: Tuple[int, int, int]
    boot_fault_code: int
    session_id: int
    sequence: int

    @property
    def state_name(self) -> str:
        return STATE_NAMES.get(self.state, f"UNKNOWN_{self.state}")

    @property
    def fault_name(self) -> str:
        return FAULT_NAMES.get(self.fault, f"UNKNOWN_{self.fault}")

    @property
    def fault_latched(self) -> bool:
        return self.state == STATE_FAULT or self.fault != 0


@dataclass(frozen=True)
class CommandStatus:
    command_type: int
    status: int
    state: int
    fault: int
    nack: bool
    session_id: int
    sequence: int

    @property
    def status_name(self) -> str:
        return STATUS_NAMES.get(self.status, f"UNKNOWN_{self.status}")


@dataclass
class ParserStats:
    packets: int = 0
    discarded_bytes: int = 0
    length_errors: int = 0
    version_errors: int = 0
    crc_errors: int = 0


def crc32_ieee(data: bytes) -> int:
    """Return the unsigned CRC-32/IEEE value used by the H60 firmware."""

    return zlib.crc32(data) & 0xFFFFFFFF


def encode_packet(packet: Packet) -> bytes:
    if not 0 <= packet.message_type <= 0xFF:
        raise ValueError("message_type must fit uint8")
    if not 0 <= packet.session_id <= 0xFFFFFFFF:
        raise ValueError("session_id must fit uint32")
    if not 0 <= packet.sequence <= 0xFFFFFFFF:
        raise ValueError("sequence must fit uint32")
    payload = bytes(packet.payload)
    if len(payload) > MAX_PAYLOAD:
        raise ValueError("payload exceeds H60 protocol maximum")
    body = struct.pack(
        "<BBHII",
        PROTOCOL_VERSION,
        packet.message_type,
        len(payload),
        packet.session_id,
        packet.sequence,
    ) + payload
    return SOF + body + struct.pack("<I", crc32_ieee(body))


class PacketParser:
    """Incrementally parse an arbitrary stream and resynchronize on errors."""

    def __init__(self) -> None:
        self._buffer = bytearray()
        self.stats = ParserStats()

    def reset(self) -> None:
        self._buffer.clear()
        self.stats = ParserStats()

    def feed(self, data: bytes) -> list[Packet]:
        self._buffer.extend(data)
        packets: list[Packet] = []
        while True:
            start = self._buffer.find(SOF)
            if start < 0:
                keep = 1 if self._buffer.endswith(SOF[:1]) else 0
                discarded = len(self._buffer) - keep
                if discarded > 0:
                    del self._buffer[:discarded]
                    self.stats.discarded_bytes += discarded
                break
            if start > 0:
                del self._buffer[:start]
                self.stats.discarded_bytes += start
            if len(self._buffer) < 6:
                break

            payload_length = struct.unpack_from("<H", self._buffer, 4)[0]
            if payload_length > MAX_PAYLOAD:
                del self._buffer[0]
                self.stats.length_errors += 1
                continue
            total = FIXED_BYTES + payload_length
            if len(self._buffer) < total:
                break

            frame = bytes(self._buffer[:total])
            if frame[2] != PROTOCOL_VERSION:
                del self._buffer[0]
                self.stats.version_errors += 1
                continue
            expected_crc = struct.unpack_from("<I", frame, HEADER_BYTES + payload_length)[0]
            actual_crc = crc32_ieee(frame[2 : HEADER_BYTES + payload_length])
            if actual_crc != expected_crc:
                del self._buffer[0]
                self.stats.crc_errors += 1
                continue

            message_type = frame[3]
            session_id, sequence = struct.unpack_from("<II", frame, 6)
            payload = frame[HEADER_BYTES : HEADER_BYTES + payload_length]
            packets.append(Packet(message_type, session_id, sequence, payload))
            del self._buffer[:total]
            self.stats.packets += 1
        return packets


def decode_telemetry(packet: Packet) -> Telemetry:
    if packet.message_type != MSG_TELEMETRY or len(packet.payload) != 40:
        raise ValueError("telemetry packet must have type 0x80 and 40-byte payload")
    values = struct.unpack("<BBBB4i4hHHBBBBI", packet.payload)
    return Telemetry(
        state=values[0],
        fault=values[1],
        motion_output_available=bool(values[2]),
        self_test_ok=bool(values[3]),
        encoder_count=tuple(values[4:8]),
        encoder_delta=tuple(values[8:12]),
        vin_raw=values[12],
        vin_nominal_mv=values[13],
        firmware_version=(values[14], values[15], values[16]),
        boot_fault_code=values[18],
        session_id=packet.session_id,
        sequence=packet.sequence,
    )


def decode_command_status(packet: Packet) -> CommandStatus:
    if packet.message_type not in (MSG_ACK, MSG_NACK) or len(packet.payload) != 4:
        raise ValueError("command status must be ACK/NACK with 4-byte payload")
    command_type, status, state, fault = packet.payload
    return CommandStatus(
        command_type=command_type,
        status=status,
        state=state,
        fault=fault,
        nack=packet.message_type == MSG_NACK,
        session_id=packet.session_id,
        sequence=packet.sequence,
    )


def encode_wheel_targets_mmps(targets: Sequence[int]) -> bytes:
    if len(targets) != 4:
        raise ValueError("exactly four H60 channel targets are required")
    checked = []
    for value in targets:
        integer = int(value)
        if integer < -32768 or integer > 32767:
            raise ValueError("wheel target must fit int16 mm/s")
        checked.append(integer)
    return struct.pack("<4h", *checked)


def differential_targets_mmps(
    linear_x_mps: float,
    angular_z_radps: float,
    track_width_m: float,
    channel_wheels: Sequence[str],
    channel_signs: Sequence[int],
    wheel_target_limit_mmps: int,
) -> Tuple[int, int, int, int]:
    """Map chassis twist to A-D wheel linear targets in integer mm/s."""

    for value, name in (
        (linear_x_mps, "linear_x_mps"),
        (angular_z_radps, "angular_z_radps"),
        (track_width_m, "track_width_m"),
    ):
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")
    if track_width_m <= 0.0:
        raise ValueError("track_width_m must be positive")
    if len(channel_wheels) != 4 or len(channel_signs) != 4:
        raise ValueError("four channel mappings and signs are required")
    if set(channel_wheels) != {"lf", "lr", "rf", "rr"}:
        raise ValueError("channel_wheels must be a permutation of lf/lr/rf/rr")
    if any(sign not in (-1, 1) for sign in channel_signs):
        raise ValueError("channel_signs must contain only -1 or 1")
    limit = int(wheel_target_limit_mmps)
    if limit <= 0 or limit > 32767:
        raise ValueError("wheel_target_limit_mmps must be in 1..32767")

    left = linear_x_mps - angular_z_radps * track_width_m / 2.0
    right = linear_x_mps + angular_z_radps * track_width_m / 2.0
    wheel_value = {"lf": left, "lr": left, "rf": right, "rr": right}
    result = []
    for wheel, sign in zip(channel_wheels, channel_signs):
        target = int(round(wheel_value[wheel] * 1000.0)) * sign
        result.append(max(-limit, min(limit, target)))
    return tuple(result)  # type: ignore[return-value]


@dataclass(frozen=True)
class MotionIntent:
    linear_x_mps: float
    angular_z_radps: float
    active: bool


@dataclass(frozen=True)
class MotionGate:
    motion_commands_enabled: bool
    wheel_mapping_confirmed: bool


@dataclass(frozen=True)
class PlannedPacket:
    packet: Optional[Packet]
    reason: str
    wheel_targets_mmps: Optional[Tuple[int, int, int, int]] = None


def _new_session_id() -> int:
    value = 0
    while value == 0:
        value = secrets.randbits(32)
    return value


class H60CommandPlanner:
    """Generate fail-safe command packets while enforcing session and ARM gates."""

    def __init__(
        self,
        *,
        heartbeat_period_ms: int = 100,
        linear_deadband_mps: float = 0.01,
        angular_deadband_radps: float = 0.02,
        session_factory: Callable[[], int] = _new_session_id,
    ) -> None:
        if heartbeat_period_ms <= 0:
            raise ValueError("heartbeat_period_ms must be positive")
        self.heartbeat_period_ms = heartbeat_period_ms
        self.linear_deadband_mps = linear_deadband_mps
        self.angular_deadband_radps = angular_deadband_radps
        self._session_factory = session_factory
        self.telemetry: Optional[Telemetry] = None
        self.last_response: Optional[CommandStatus] = None
        self.reset()

    def reset(self) -> None:
        session_id = int(self._session_factory())
        if session_id <= 0 or session_id > 0xFFFFFFFF:
            raise ValueError("session_factory must return a non-zero uint32")
        self.session_id = session_id
        self._next_sequence = 1
        self._last_heartbeat_ms: Optional[int] = None
        self._session_ready = False
        self._centered_seen = False
        self._arm_pending = False
        self._stop_required = True
        self._intent_was_active = False
        self._device_motion_locked = False
        self.telemetry = None
        self.last_response = None

    @property
    def session_ready(self) -> bool:
        return self._session_ready

    @property
    def armed(self) -> bool:
        return self.telemetry is not None and self.telemetry.state == STATE_ARMED

    @property
    def device_motion_ready(self) -> bool:
        telemetry = self.telemetry
        return bool(
            telemetry is not None
            and telemetry.self_test_ok
            and telemetry.motion_output_available
            and not self._device_motion_locked
            and not telemetry.fault_latched
            and telemetry.state in (STATE_DISARMED, STATE_ARMED)
        )

    def _sequence(self) -> int:
        value = self._next_sequence
        if value == 0 or value > 0xFFFFFFFF:
            raise OverflowError("H60 command sequence exhausted; rotate session")
        self._next_sequence += 1
        return value

    def _heartbeat(self, now_ms: int) -> Packet:
        self._last_heartbeat_ms = now_ms
        return Packet(MSG_HEARTBEAT, self.session_id, self._sequence())

    def _rotate_after_stop(self) -> None:
        session_id = int(self._session_factory())
        if session_id <= 0 or session_id > 0xFFFFFFFF:
            raise ValueError("session_factory must return a non-zero uint32")
        self.session_id = session_id
        self._next_sequence = 1
        self._last_heartbeat_ms = None
        self._session_ready = False
        self._centered_seen = False
        self._arm_pending = False

    def observe(self, packet: Packet) -> None:
        if packet.message_type == MSG_TELEMETRY:
            telemetry = decode_telemetry(packet)
            self.telemetry = telemetry
            self._device_motion_locked = not telemetry.motion_output_available
            session_healthy = (
                telemetry.session_id == self.session_id
                and telemetry.self_test_ok
                and telemetry.state in (STATE_DISARMED, STATE_ARMED)
                and not telemetry.fault_latched
            )
            if session_healthy:
                self._session_ready = True
            elif self._session_ready and telemetry.session_id != self.session_id:
                self._rotate_after_stop()
                self._stop_required = True
                self._intent_was_active = False
            else:
                self._session_ready = False
            if telemetry.state == STATE_ARMED:
                self._arm_pending = False
            return
        if packet.message_type not in (MSG_ACK, MSG_NACK):
            return
        response = decode_command_status(packet)
        self.last_response = response
        if response.command_type == MSG_HEARTBEAT and not response.nack:
            if (
                response.session_id == self.session_id
                and response.status == STATUS_OK
            ):
                self._session_ready = True
        elif response.command_type == MSG_ARM:
            if response.session_id != self.session_id:
                return
            if response.nack:
                self._arm_pending = False
                if response.status == STATUS_MOTION_LOCKED:
                    self._device_motion_locked = True
            elif response.status == STATUS_OK:
                # ACK confirms command acceptance, but ARMED telemetry is the
                # authoritative state transition. Do not send a second ARM in
                # the acknowledgement-to-telemetry window.
                self._arm_pending = True
        elif response.command_type in (MSG_STOP, MSG_DISARM) and not response.nack:
            self._session_ready = False

    def plan(
        self,
        *,
        now_ms: int,
        intent: MotionIntent,
        command_fresh: bool,
        gate: MotionGate,
        track_width_m: float,
        channel_wheels: Sequence[str],
        channel_signs: Sequence[int],
        wheel_target_limit_mmps: int,
    ) -> PlannedPacket:
        if self._stop_required:
            self._stop_required = False
            return PlannedPacket(Packet(MSG_STOP), "initial_stop")

        if not command_fresh or not intent.active:
            if self._intent_was_active or self.armed or self._arm_pending:
                self._intent_was_active = False
                self._rotate_after_stop()
                return PlannedPacket(Packet(MSG_STOP), "inactive_stop")
            if self._heartbeat_due(now_ms):
                return PlannedPacket(self._heartbeat(now_ms), "idle_heartbeat")
            return PlannedPacket(None, "idle")

        self._intent_was_active = True
        centered = (
            abs(intent.linear_x_mps) <= self.linear_deadband_mps
            and abs(intent.angular_z_radps) <= self.angular_deadband_radps
        )

        if not gate.motion_commands_enabled:
            return self._heartbeat_or_none(now_ms, "motion_commands_disabled")
        if not gate.wheel_mapping_confirmed:
            return self._heartbeat_or_none(now_ms, "wheel_mapping_unconfirmed")
        if not self.device_motion_ready:
            return self._heartbeat_or_none(now_ms, "device_motion_not_ready")
        if not self._session_ready:
            return self._heartbeat_or_none(now_ms, "session_not_ready")
        if centered:
            self._centered_seen = True
        if not self._centered_seen:
            return self._heartbeat_or_none(now_ms, "input_not_centered")

        targets = differential_targets_mmps(
            intent.linear_x_mps,
            intent.angular_z_radps,
            track_width_m,
            channel_wheels,
            channel_signs,
            wheel_target_limit_mmps,
        )
        if not self.armed:
            if centered:
                return self._heartbeat_or_none(now_ms, "centered_ready")
            if self._arm_pending:
                return self._heartbeat_or_none(now_ms, "arm_pending")
            packet = Packet(MSG_ARM, self.session_id, self._sequence())
            self._arm_pending = True
            return PlannedPacket(packet, "arm_requested")

        if self._heartbeat_due(now_ms):
            return PlannedPacket(self._heartbeat(now_ms), "armed_heartbeat")
        packet = Packet(
            MSG_WHEEL_TARGET,
            self.session_id,
            self._sequence(),
            encode_wheel_targets_mmps(targets),
        )
        return PlannedPacket(packet, "wheel_target", targets)

    def _heartbeat_due(self, now_ms: int) -> bool:
        return (
            self._last_heartbeat_ms is None
            or now_ms - self._last_heartbeat_ms >= self.heartbeat_period_ms
        )

    def _heartbeat_or_none(self, now_ms: int, reason: str) -> PlannedPacket:
        if self._heartbeat_due(now_ms):
            return PlannedPacket(self._heartbeat(now_ms), reason)
        return PlannedPacket(None, reason)
