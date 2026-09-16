"""State machine for the no-Orin W0 web teleop backend."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import time
from typing import Any, Protocol


class TeleopIntent(str, Enum):
    STOP = "STOP"
    DISARM = "DISARM"
    ARM_REQUEST = "ARM_REQUEST"
    FORWARD_LOW = "FORWARD_LOW"
    REVERSE_LOW = "REVERSE_LOW"


class BackendState(str, Enum):
    DISARMED = "DISARMED"
    ARM_PENDING = "ARM_PENDING"
    ARMED = "ARMED"
    FAULT = "FAULT"


@dataclass(frozen=True)
class ControllerConfig:
    command_lease_ms: int = 220
    max_loop_gap_ms: int = 120
    max_events: int = 500
    defer_arm_until_motion: bool = False
    arm_request_lease_ms: int = 5000
    field_auto_stop_ms: int | None = None


@dataclass(frozen=True)
class IntentResult:
    accepted: bool
    state: str
    reason: str
    active_direction: str | None
    fault_reason: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "state": self.state,
            "reason": self.reason,
            "active_direction": self.active_direction,
            "fault_reason": self.fault_reason,
        }


class H60Link(Protocol):
    commands: list[dict[str, Any]]

    def status(self) -> Any:
        ...

    def send(self, command: str, *, now_ms: int, reason: str) -> dict[str, Any]:
        ...


def monotonic_ms() -> int:
    return int(time.monotonic() * 1000.0)


class WebTeleopController:
    """Convert browser intents into a fake-serial W0 control session."""

    def __init__(self, h60: H60Link, *, config: ControllerConfig | None = None) -> None:
        self.h60 = h60
        self.config = config or ControllerConfig()
        if self.config.command_lease_ms <= 0:
            raise ValueError("command_lease_ms must be positive")
        if self.config.max_loop_gap_ms <= 0:
            raise ValueError("max_loop_gap_ms must be positive")
        if self.config.arm_request_lease_ms <= 0:
            raise ValueError("arm_request_lease_ms must be positive")
        if self.config.field_auto_stop_ms is not None and self.config.field_auto_stop_ms <= 0:
            raise ValueError("field_auto_stop_ms must be positive")
        self.state = BackendState.DISARMED
        self.active_direction: str | None = None
        self.active_client: str | None = None
        self.lease_deadline_ms: int | None = None
        self.active_started_ms: int | None = None
        self.pending_arm_deadline_ms: int | None = None
        self.pending_arm_client: str | None = None
        self.last_loop_ms: int | None = None
        self.fault_reason: str | None = None
        self._last_session_epoch: int | None = self._current_session_epoch()
        self._client_sequences: dict[str, int] = {}
        self._closed_clients: set[str] = set()
        self.events: list[dict[str, Any]] = []

    def handle_intent(
        self,
        intent_name: str,
        *,
        now_ms: int | None = None,
        client_id: str = "browser",
        sequence: int | None = None,
    ) -> IntentResult:
        now = monotonic_ms() if now_ms is None else int(now_ms)
        try:
            intent = TeleopIntent(intent_name)
        except ValueError:
            self._record(now, "reject", intent=intent_name, reason="unknown_intent")
            return self._result(False, "unknown_intent")

        if client_id in self._closed_clients and intent not in (
            TeleopIntent.STOP, TeleopIntent.DISARM
        ):
            self._record(now, "reject", intent=intent.value, client_id=client_id,
                         reason="client_session_closed")
            return self._result(False, "client_session_closed")

        if not self._sequence_is_acceptable(intent, client_id, sequence):
            self._record(
                now,
                "reject",
                intent=intent.value,
                client_id=client_id,
                sequence=sequence,
                reason="stale_sequence",
            )
            return self._result(False, "stale_sequence")

        self._record(
            now,
            "intent",
            intent=intent.value,
            client_id=client_id,
            sequence=sequence,
        )

        if intent == TeleopIntent.STOP:
            response = self._send("STOP", now, "web_stop")
            block = self._link_block_reason()
            if not response.get("ack") or block is not None:
                return self._fault(now, block or str(response.get("response_reason", "stop_rejected")))
            self._clear_active_motion()
            if self.state != BackendState.FAULT:
                self.state = BackendState.DISARMED
            return self._result(True, "stop")

        if intent == TeleopIntent.DISARM:
            stop = self._send("STOP", now, "web_disarm_pre_stop")
            disarm = self._send("DISARM", now, "web_disarm")
            block = self._link_block_reason()
            if not stop.get("ack") or not disarm.get("ack") or block is not None:
                return self._fault(now, block or str(
                    stop.get("response_reason") if not stop.get("ack")
                    else disarm.get("response_reason", "disarm_rejected")
                ))
            self._clear_active_motion()
            self.state = BackendState.DISARMED
            self.fault_reason = None
            return self._result(True, "disarm")

        tick_result = self.tick(now_ms=now)

        if client_id in self._closed_clients:
            return self._result(False, "client_session_closed")
        if tick_result.reason != "tick":
            return tick_result

        if self.fault_reason is not None:
            return self._result(False, "fault_latched")

        link_reason = self._link_block_reason()
        if link_reason is not None:
            return self._fault(now, link_reason)

        if intent == TeleopIntent.ARM_REQUEST:
            if self.active_direction is not None:
                response = self._send("STOP", now, "arm_requires_neutral")
                block = self._link_block_reason()
                if not response.get("ack") or block is not None:
                    return self._fault(now, block or str(response.get("response_reason", "stop_rejected")))
                self._clear_active_motion()
                return self._result(False, "arm_requires_neutral")
            if self.config.defer_arm_until_motion:
                if self.pending_arm_client not in (None, client_id):
                    return self._result(False, "arm_client_mismatch")
                self.state = BackendState.ARM_PENDING
                self.pending_arm_client = client_id
                self.pending_arm_deadline_ms = now + self.config.arm_request_lease_ms
                return self._result(True, "arm_pending")
            response = self._send("ARM", now, "web_arm_request")
            if response.get("ack"):
                self.state = BackendState.ARMED
                return self._result(True, "armed")
            return self._fault(now, str(response.get("response_reason", "arm_rejected")))

        direction = "forward" if intent == TeleopIntent.FORWARD_LOW else "reverse"
        if self.state == BackendState.ARM_PENDING:
            if self.pending_arm_client != client_id:
                return self._result(False, "arm_client_mismatch")
            if self.pending_arm_deadline_ms is None or now >= self.pending_arm_deadline_ms:
                self._clear_active_motion()
                self.state = BackendState.DISARMED
                return self._result(False, "arm_request_expired")
            status = self.h60.status()
            status_data = status.as_dict() if hasattr(status, "as_dict") else status
            if status_data.get("field_plan_id") and status_data.get("allowed_direction") != direction:
                self._clear_active_motion()
                self.state = BackendState.DISARMED
                return self._result(False, "direction_not_enabled")
            response = self._send("ARM", now, "web_arm_request_on_direction_hold")
            if not response.get("ack"):
                return self._fault(now, str(response.get("response_reason", "arm_rejected")))
            self.state = BackendState.ARMED
            self.pending_arm_deadline_ms = None
            self.pending_arm_client = None
        if self.state != BackendState.ARMED:
            self._record(now, "reject", intent=intent.value, reason="not_armed")
            return self._result(False, "not_armed")

        if self.active_direction and self.active_direction != direction:
            response = self._send("STOP", now, "direction_change_requires_neutral")
            block = self._link_block_reason()
            if not response.get("ack") or block is not None:
                return self._fault(now, block or str(response.get("response_reason", "stop_rejected")))
            self._clear_active_motion()
            self.state = BackendState.DISARMED
            return self._result(False, "direction_change_requires_neutral")

        if self._field_motion_window_elapsed(now):
            return self._field_auto_stop(now)

        command = "PROFILE_FORWARD_LOW" if direction == "forward" else "PROFILE_REVERSE_LOW"
        response = self._send(command, now, f"lease_{direction}")
        if not response.get("ack"):
            return self._fault(now, str(response.get("response_reason", "profile_rejected")))
        self.active_direction = direction
        if self.active_started_ms is None:
            self.active_started_ms = now
        self.active_client = client_id
        self.lease_deadline_ms = now + self.config.command_lease_ms
        return self._result(True, f"{direction}_lease_renewed")

    def tick(self, *, now_ms: int | None = None) -> IntentResult:
        now = monotonic_ms() if now_ms is None else int(now_ms)
        if (
            self.last_loop_ms is not None
            and self.active_direction is not None
            and now - self.last_loop_ms > self.config.max_loop_gap_ms
        ):
            return self._fault(now, "backend_loop_late")

        link_reason = self._link_block_reason()
        if (self.active_direction is not None or self.state == BackendState.ARM_PENDING) and link_reason is not None:
            return self._fault(now, link_reason)

        if self._field_motion_window_elapsed(now):
            self.last_loop_ms = now
            return self._field_auto_stop(now)

        if (
            self.state == BackendState.ARM_PENDING
            and self.pending_arm_deadline_ms is not None
            and now >= self.pending_arm_deadline_ms
        ):
            self._clear_active_motion()
            self.state = BackendState.DISARMED
            self.last_loop_ms = now
            return self._result(True, "arm_request_expired")

        if (
            self.active_direction is not None
            and self.lease_deadline_ms is not None
            and now >= self.lease_deadline_ms
        ):
            if self.active_client is not None:
                self._closed_clients.add(self.active_client)
            response = self._send("STOP", now, "lease_expired")
            self._clear_active_motion()
            block = self._link_block_reason()
            if not response.get("ack") or block is not None:
                return self._fault(now, block or str(response.get("response_reason", "stop_rejected")))
            self.state = BackendState.DISARMED
            self.last_loop_ms = now
            return self._result(True, "lease_expired_stop")

        self.last_loop_ms = now
        return self._result(True, "tick")

    def client_disconnect(
        self, *, client_id: str = "browser", now_ms: int | None = None
    ) -> IntentResult:
        now = monotonic_ms() if now_ms is None else int(now_ms)
        self._record(now, "disconnect", client_id=client_id)
        self._closed_clients.add(client_id)
        stop = self._send("STOP", now, "client_disconnect")
        disarm = self._send("DISARM", now, "client_disconnect")
        block = self._link_block_reason()
        if not stop.get("ack") or not disarm.get("ack") or block is not None:
            return self._fault(now, block or str(
                stop.get("response_reason") if not stop.get("ack")
                else disarm.get("response_reason", "disarm_rejected")
            ))
        self._clear_active_motion()
        if self.state != BackendState.FAULT:
            self.state = BackendState.DISARMED
        return self._result(True, "disconnect_stop_disarm")

    def set_fake_scenario(self, scenario: str, *, now_ms: int | None = None) -> None:
        now = monotonic_ms() if now_ms is None else int(now_ms)
        setter = getattr(self.h60, "set_scenario", None)
        if setter is None:
            raise RuntimeError("attached H60 link does not expose fake scenarios")
        setter(scenario)
        self._record(now, "fake_scenario", scenario=scenario)

    def audit_failure(self, *, now_ms: int | None = None) -> IntentResult:
        """Fail closed if a sent command cannot be written to the audit log."""

        now = monotonic_ms() if now_ms is None else int(now_ms)
        return self._fault(now, "audit_log_failure")

    def export_state(self, *, now_ms: int | None = None) -> dict[str, Any]:
        now = monotonic_ms() if now_ms is None else int(now_ms)
        self.tick(now_ms=now)
        status = self.h60.status()
        lease_remaining_ms = 0
        if self.lease_deadline_ms is not None:
            lease_remaining_ms = max(0, self.lease_deadline_ms - now)
        elif self.pending_arm_deadline_ms is not None:
            lease_remaining_ms = max(0, self.pending_arm_deadline_ms - now)
        return {
            "state": self.state.value,
            "active_direction": self.active_direction,
            "active_client": self.active_client,
            "fault_reason": self.fault_reason,
            "lease_remaining_ms": lease_remaining_ms,
            "h60": status.as_dict() if hasattr(status, "as_dict") else status,
            "commands": self.h60.commands[-40:],
            "events": self.events[-80:],
        }

    def _sequence_is_acceptable(
        self, intent: TeleopIntent, client_id: str, sequence: int | None
    ) -> bool:
        if sequence is None:
            return True
        seq = int(sequence)
        last = self._client_sequences.get(client_id)
        if last is not None and seq <= last and intent not in (
            TeleopIntent.STOP,
            TeleopIntent.DISARM,
        ):
            return False
        self._client_sequences[client_id] = max(seq, last or seq)
        return True

    def _link_block_reason(self) -> str | None:
        status = self.h60.status()
        data = status.as_dict() if hasattr(status, "as_dict") else status
        epoch = data.get("session_epoch")
        if epoch is not None:
            epoch = int(epoch)
            if self._last_session_epoch is None:
                self._last_session_epoch = epoch
            elif epoch != self._last_session_epoch:
                self._last_session_epoch = epoch
                if self.active_direction is not None or self.state in (BackendState.ARM_PENDING, BackendState.ARMED):
                    return "h60_reboot"
        if not data.get("identity_ok", False):
            return "identity_drift"
        if not data.get("telemetry_fresh", False):
            return "telemetry_timeout"
        if data.get("protocol_error"):
            return str(data["protocol_error"])
        if data.get("fault") or data.get("state") == "FAULT":
            return "h60_fault"
        return None

    def _current_session_epoch(self) -> int | None:
        status = self.h60.status()
        data = status.as_dict() if hasattr(status, "as_dict") else status
        epoch = data.get("session_epoch")
        return None if epoch is None else int(epoch)

    def _fault(self, now: int, reason: str) -> IntentResult:
        for client in (self.active_client, self.pending_arm_client):
            if client is not None:
                self._closed_clients.add(client)
        if self.active_direction is not None or self.state == BackendState.ARMED:
            self._send("STOP", now, f"fault_{reason}")
        self._clear_active_motion()
        self.state = BackendState.FAULT
        self.fault_reason = reason
        self._record(now, "fault_latched", reason=reason)
        return self._result(False, reason)

    def _field_motion_window_elapsed(self, now: int) -> bool:
        limit = self.config.field_auto_stop_ms
        return (
            limit is not None
            and self.active_direction is not None
            and self.active_started_ms is not None
            and now - self.active_started_ms >= limit
        )

    def _field_auto_stop(self, now: int) -> IntentResult:
        response = self._send("STOP", now, "field_auto_stop")
        client = self.active_client
        self._clear_active_motion()
        block = self._link_block_reason()
        if not response.get("ack") or block is not None:
            if client is not None:
                self._closed_clients.add(client)
            return self._fault(now, block or str(response.get("response_reason", "stop_rejected")))
        self.state = BackendState.DISARMED
        return self._result(True, "field_auto_stop")

    def _send(self, command: str, now: int, reason: str) -> dict[str, Any]:
        response = self.h60.send(command, now_ms=now, reason=reason)
        self._record(now, "h60_command", **response)
        return response

    def _clear_active_motion(self) -> None:
        self.active_direction = None
        self.active_started_ms = None
        self.active_client = None
        self.lease_deadline_ms = None
        self.pending_arm_client = None
        self.pending_arm_deadline_ms = None

    def _record(self, now: int, event: str, **fields: Any) -> None:
        self.events.append({"now_ms": now, "event": event, **fields})
        overflow = len(self.events) - self.config.max_events
        if overflow > 0:
            del self.events[:overflow]

    def _result(self, accepted: bool, reason: str) -> IntentResult:
        return IntentResult(
            accepted=accepted,
            state=self.state.value,
            reason=reason,
            active_direction=self.active_direction,
            fault_reason=self.fault_reason,
        )
