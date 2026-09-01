"""ROS-independent command arbitration state machine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MotionInput:
    linear_x_mps: float
    angular_z_radps: float
    active: bool
    received_at: float
    sequence: int = 0


@dataclass(frozen=True)
class ArbitrationResult:
    linear_x_mps: float
    angular_z_radps: float
    active: bool
    source: str
    reason: str


class CommandArbiter:
    """Select manual or autonomy input with fail-safe timeout behavior."""

    def __init__(
        self,
        *,
        manual_timeout_sec: float,
        autonomy_timeout_sec: float,
        manual_release_hold_sec: float,
        autonomy_enabled: bool,
    ) -> None:
        self.manual_timeout_sec = manual_timeout_sec
        self.autonomy_timeout_sec = autonomy_timeout_sec
        self.manual_release_hold_sec = manual_release_hold_sec
        self.autonomy_enabled = autonomy_enabled
        self.base_comm_ok = False
        self.base_motion_ready = False
        self.software_motion_lock_latched = False
        self.software_motion_lock_reason = ""
        self.manual: Optional[MotionInput] = None
        self.autonomy: Optional[MotionInput] = None
        self._manual_owned = False
        self._manual_release_at = float("-inf")
        self._autonomy_must_be_newer_than = float("-inf")

    def update_manual(self, command: MotionInput) -> None:
        self.manual = command
        if command.active:
            self._manual_owned = True

    def update_autonomy(self, command: MotionInput) -> None:
        self.autonomy = command

    def latch_motion_lock(self, reason: str) -> None:
        self.software_motion_lock_latched = True
        self.software_motion_lock_reason = reason or "unspecified"

    def clear_motion_lock(self) -> None:
        self.software_motion_lock_latched = False
        self.software_motion_lock_reason = ""
        self.manual = None
        self.autonomy = None
        self._manual_owned = False
        self._manual_release_at = float("-inf")
        self._autonomy_must_be_newer_than = float("-inf")

    def update_base_state(self, *, comm_ok: bool, motion_ready: bool) -> None:
        self.base_comm_ok = comm_ok
        self.base_motion_ready = motion_ready
        if not comm_ok or not motion_ready:
            self._manual_owned = False

    @staticmethod
    def _fresh(command: Optional[MotionInput], now: float, timeout: float) -> bool:
        return command is not None and 0.0 <= now - command.received_at <= timeout

    @staticmethod
    def _stop(reason: str) -> ArbitrationResult:
        return ArbitrationResult(0.0, 0.0, False, "safety", reason)

    def decide(self, now: float) -> ArbitrationResult:
        if self.software_motion_lock_latched:
            return self._stop("software_motion_lock_latched")
        if not self.base_comm_ok:
            return self._stop("base_communication_unavailable")
        if not self.base_motion_ready:
            return self._stop("base_motion_not_ready")

        manual_fresh = self._fresh(self.manual, now, self.manual_timeout_sec)
        manual_active = manual_fresh and self.manual is not None and self.manual.active
        if manual_active:
            self._manual_owned = True
            return ArbitrationResult(
                self.manual.linear_x_mps,
                self.manual.angular_z_radps,
                True,
                "manual",
                "manual_takeover",
            )

        if self._manual_owned:
            self._manual_owned = False
            self._manual_release_at = now
            self._autonomy_must_be_newer_than = now

        if now - self._manual_release_at < self.manual_release_hold_sec:
            return self._stop("manual_release_hold")

        if not self.autonomy_enabled:
            return self._stop("autonomy_disabled")

        autonomy_fresh = self._fresh(self.autonomy, now, self.autonomy_timeout_sec)
        autonomy_valid = (
            autonomy_fresh
            and self.autonomy is not None
            and self.autonomy.active
            and self.autonomy.received_at > self._autonomy_must_be_newer_than
        )
        if autonomy_valid:
            return ArbitrationResult(
                self.autonomy.linear_x_mps,
                self.autonomy.angular_z_radps,
                True,
                "autonomy",
                "autonomy_selected",
            )
        return self._stop("no_fresh_command")
