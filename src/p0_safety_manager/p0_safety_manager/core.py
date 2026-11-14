"""ROS-independent command arbitration state machine."""

from __future__ import annotations

from dataclasses import dataclass
import math
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


@dataclass(frozen=True)
class ModePermission:
    mode: str
    motion_allowed: bool
    fault_latched: bool
    epoch: str
    generation: int
    received_at: float


class CommandArbiter:
    """Select manual or autonomy input with fail-safe timeout behavior."""

    def __init__(
        self,
        *,
        manual_timeout_sec: float,
        autonomy_timeout_sec: float,
        manual_release_hold_sec: float,
        autonomy_enabled: bool,
        require_system_mode: bool = False,
        system_mode_timeout_sec: float = .25,
    ) -> None:
        self.manual_timeout_sec = manual_timeout_sec
        self.autonomy_timeout_sec = autonomy_timeout_sec
        self.manual_release_hold_sec = manual_release_hold_sec
        self.autonomy_enabled = autonomy_enabled
        self.require_system_mode = require_system_mode
        self.system_mode_timeout_sec = system_mode_timeout_sec
        self.system_mode: Optional[ModePermission] = None
        self._neutral_required = require_system_mode
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
        if self.require_system_mode:
            if not self._mode_allows_motion(command.received_at):
                self._discard_intent()
                return
            if self._neutral_required:
                if (not command.active and command.linear_x_mps == 0 and command.angular_z_radps == 0):
                    self._neutral_required = False
                    self.manual = command
                return
        self.manual = command
        if command.active:
            self._manual_owned = True

    def update_autonomy(self, command: MotionInput) -> None:
        self.autonomy = command

    def _discard_intent(self) -> None:
        self.manual = self.autonomy = None
        self._manual_owned = False
        self._manual_release_at = float('-inf')
        self._autonomy_must_be_newer_than = float('-inf')
        self._neutral_required = self.require_system_mode

    def _mode_allows_motion(self, now) -> bool:
        state = self.system_mode
        return (self._fresh(state, now, self.system_mode_timeout_sec) and
                state.mode == 'MANUAL' and state.motion_allowed and not state.fault_latched)

    def update_system_mode(self, state: ModePermission) -> None:
        if (state.mode not in ('STANDBY', 'MANUAL', 'FAULT') or not state.epoch or
                type(state.generation) is not int or state.generation < 0 or
                not math.isfinite(state.received_at) or
                (state.motion_allowed and (state.mode != 'MANUAL' or state.fault_latched))):
            self.system_mode = None
            self._discard_intent()
            return
        old = self.system_mode
        if old is not None and old.epoch == state.epoch and state.generation < old.generation:
            return  # 迟到状态不刷新接收时刻。
        if (old is None or (old.epoch, old.generation, old.mode, old.motion_allowed, old.fault_latched) !=
                (state.epoch, state.generation, state.mode, state.motion_allowed, state.fault_latched) or
                not self._fresh(old, state.received_at, self.system_mode_timeout_sec)):
            self._discard_intent()
        self.system_mode = state

    def latch_motion_lock(self, reason: str) -> None:
        self.software_motion_lock_latched = True
        self.software_motion_lock_reason = reason or "unspecified"

    def clear_motion_lock(self) -> None:
        self.software_motion_lock_latched = False
        self.software_motion_lock_reason = ""
        self._discard_intent()

    def update_base_state(self, *, comm_ok: bool, motion_ready: bool) -> None:
        self.base_comm_ok = comm_ok
        self.base_motion_ready = motion_ready
        if not comm_ok or not motion_ready:
            self._manual_owned = False
            if self.require_system_mode:
                self._discard_intent()

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
        if self.require_system_mode and not self._mode_allows_motion(now):
            self._discard_intent()
            return self._stop('system_mode_not_allowed_or_stale')

        manual_fresh = self._fresh(self.manual, now, self.manual_timeout_sec)
        manual_active = manual_fresh and self.manual is not None and self.manual.active
        if manual_active:
            if not all(math.isfinite(v) for v in (self.manual.linear_x_mps, self.manual.angular_z_radps)):
                self.latch_motion_lock('non_finite_manual_command')
                return self._stop('software_motion_lock_latched')
            self._manual_owned = True
            return ArbitrationResult(
                self.manual.linear_x_mps,
                self.manual.angular_z_radps,
                True,
                "manual",
                "manual_takeover",
            )

        if self.require_system_mode:
            # P2的MANUAL许可不能用于自动源；失效/清锁/重启后必须重新松使能并归零。
            if not manual_fresh:
                self._discard_intent()
            return self._stop('manual_neutral_required' if self._neutral_required else 'no_fresh_manual_command')

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
