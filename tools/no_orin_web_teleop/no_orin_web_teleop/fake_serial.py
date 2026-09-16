"""Offline fake H60 serial link for W0 web-teleop validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any


def _ensure_bridge_path() -> None:
    repo = Path(__file__).resolve().parents[3]
    package_path = repo / "src" / "p0_base_bridge"
    if package_path.exists() and str(package_path) not in sys.path:
        sys.path.insert(0, str(package_path))


_ensure_bridge_path()

from p0_base_bridge.h60_protocol import (  # noqa: E402
    MSG_ARM,
    MSG_DISARM,
    MSG_M2A_CALIBRATION_HOLD,
    MSG_STOP,
    Packet,
    encode_packet,
    encode_w2_four_wheel_profile,
)


VALID_SCENARIOS = {
    "normal",
    "fault",
    "timeout",
    "identity_drift",
    "reboot",
    "crc_error",
    "length_error",
    "sequence_error",
}
REAL_FRAME_COMMANDS = {
    "STOP": MSG_STOP,
    "DISARM": MSG_DISARM,
    "ARM": MSG_ARM,
}


@dataclass(frozen=True)
class FakeH60Status:
    identity_ok: bool
    telemetry_fresh: bool
    state: str
    fault: bool
    firmware_version: str
    identity: str
    session_epoch: int
    scenario: str
    protocol_error: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "identity_ok": self.identity_ok,
            "telemetry_fresh": self.telemetry_fresh,
            "state": self.state,
            "fault": self.fault,
            "firmware_version": self.firmware_version,
            "identity": self.identity,
            "session_epoch": self.session_epoch,
            "scenario": self.scenario,
            "protocol_error": self.protocol_error,
        }


class FakeH60Serial:
    """A deterministic fake link with no device discovery or file descriptors."""

    def __init__(self, *, identity: str = "FAKE-H60-W0") -> None:
        self.identity = identity
        self.scenario = "normal"
        self.state = "DISARMED"
        self.session_epoch = 1
        self._packet_session = 0x500001
        self._packet_sequence = 1
        self.commands: list[dict[str, Any]] = []

    def set_scenario(self, scenario: str) -> None:
        if scenario not in VALID_SCENARIOS:
            raise ValueError(f"unknown fake serial scenario: {scenario}")
        if scenario == "reboot":
            self.session_epoch += 1
            self.state = "DISARMED"
        self.scenario = scenario

    def clear(self) -> None:
        self.scenario = "normal"
        self.state = "DISARMED"

    def status(self) -> FakeH60Status:
        scenario = self.scenario
        return FakeH60Status(
            identity_ok=scenario != "identity_drift",
            telemetry_fresh=scenario != "timeout",
            state="FAULT" if scenario == "fault" else self.state,
            fault=scenario == "fault",
            firmware_version="0.0.0-fake-w0",
            identity=self.identity,
            session_epoch=self.session_epoch,
            scenario=scenario,
            protocol_error=scenario if scenario in {"crc_error", "length_error", "sequence_error"} else None,
        )

    def send(self, command: str, *, now_ms: int, reason: str) -> dict[str, Any]:
        scenario = self.scenario
        status = self.status()
        ack = True
        response_reason = "ok"

        if not status.identity_ok:
            ack = False
            response_reason = "identity_drift"
        elif not status.telemetry_fresh:
            ack = False
            response_reason = "telemetry_timeout"
        elif status.protocol_error is not None:
            ack = False
            response_reason = status.protocol_error
        elif command == "ARM":
            if status.fault or self.state != "DISARMED":
                ack = False
                response_reason = "arm_rejected"
            else:
                self.state = "ARMED"
        elif command in ("PROFILE_FORWARD_LOW", "PROFILE_REVERSE_LOW"):
            if status.fault:
                ack = False
                response_reason = "fault_latched"
            elif self.state != "ARMED":
                ack = False
                response_reason = "not_armed"
        elif command in ("STOP", "DISARM"):
            if scenario != "fault":
                self.state = "DISARMED"
        else:
            ack = False
            response_reason = "unknown_fake_command"

        frame_hex = self._frame_hex(command)
        record = {
            "now_ms": now_ms,
            "command": command,
            "reason": reason,
            "ack": ack,
            "response_reason": response_reason,
            "scenario": scenario,
            "state_after": self.status().state,
            "frame_hex": frame_hex,
        }
        self.commands.append(record)
        return record

    def _frame_hex(self, command: str) -> str | None:
        message_type = REAL_FRAME_COMMANDS.get(command)
        payload = b""
        if command == "PROFILE_FORWARD_LOW":
            message_type = MSG_M2A_CALIBRATION_HOLD
            payload = encode_w2_four_wheel_profile(1)
        elif command == "PROFILE_REVERSE_LOW":
            message_type = MSG_M2A_CALIBRATION_HOLD
            payload = encode_w2_four_wheel_profile(-1)
        if message_type is None:
            return None
        packet = Packet(
            message_type=message_type,
            session_id=self._packet_session,
            sequence=self._packet_sequence,
            payload=payload,
        )
        self._packet_sequence += 1
        return encode_packet(packet).hex()
