"""P2模式状态机；不发运动指令，不打开设备，不代替底层ARM或最终安全仲裁。"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class BaseState:
    comm_ok: bool
    motion_ready: bool
    fault_latched: bool
    received_at: float


@dataclass(frozen=True)
class ManualState:
    active: bool
    linear_x_mps: float
    angular_z_radps: float
    received_at: float


@dataclass(frozen=True)
class ModeState:
    mode: str
    motion_allowed: bool
    fault_latched: bool
    base_comm_ok: bool
    base_motion_ready: bool
    manual_input_fresh: bool
    reason: str
    epoch: str
    generation: int


class SystemModeManager:
    """模式权唯一归本类所属节点；本阶段仅待机、手动、故障锁止。"""
    def __init__(self, *, epoch, base_timeout_sec=.35, manual_timeout_sec=.25):
        if not epoch or any(not math.isfinite(v) or v <= 0
                            for v in (base_timeout_sec, manual_timeout_sec)):
            raise ValueError('invalid mode manager identity or timeout')
        self.epoch = epoch
        self.base_timeout_sec = base_timeout_sec
        self.manual_timeout_sec = manual_timeout_sec
        self.mode = 'STANDBY'
        self.reason = 'startup_standby'
        self.generation = 0
        self.base = None
        self.manual = None

    @staticmethod
    def _fresh(value, now, timeout):
        return value is not None and 0 <= now-value.received_at <= timeout

    def update_base(self, state): self.base = state
    def update_manual(self, state): self.manual = state

    def _manual_valid(self, now):
        return (self._fresh(self.manual, now, self.manual_timeout_sec) and
                math.isfinite(self.manual.linear_x_mps) and math.isfinite(self.manual.angular_z_radps))

    def _neutral(self, now):
        return (self._manual_valid(now) and not self.manual.active and
                self.manual.linear_x_mps == 0 and self.manual.angular_z_radps == 0)

    def _transition(self, mode, reason):
        if self.mode != mode:
            self.generation += 1
        self.mode, self.reason = mode, reason

    def evaluate(self, now):
        base_fresh = self._fresh(self.base, now, self.base_timeout_sec)
        comm_ok = base_fresh and self.base.comm_ok
        ready = comm_ok and self.base.motion_ready and not self.base.fault_latched
        manual_fresh = self._manual_valid(now)
        # 硬件故障不能由STANDBY遮盖；通信未上线则允许启动待机，禁止请求手动。
        if base_fresh and self.base.fault_latched:
            self._transition('FAULT', 'base_fault_latched')
        elif self.mode == 'MANUAL' and not ready:
            self._transition('FAULT', 'base_unavailable_or_not_ready')
        elif self.mode == 'MANUAL' and not manual_fresh:
            self._transition('FAULT', 'manual_input_unavailable')
        return ModeState(self.mode, self.mode == 'MANUAL' and ready and manual_fresh,
            self.mode == 'FAULT', bool(comm_ok), bool(ready), bool(manual_fresh),
            self.reason, self.epoch, self.generation)

    def request_mode(self, target_mode, now):
        self.evaluate(now)
        target = target_mode.strip().upper()
        if target not in ('STANDBY', 'MANUAL', 'FAULT'):
            return False, 'mode_not_supported_in_P2'
        if target == 'FAULT':
            self._transition('FAULT', 'explicit_fault_request')
            return True, self.reason
        if target == 'STANDBY':
            if self.mode == 'FAULT':
                if not (self._fresh(self.base, now, self.base_timeout_sec) and
                        self.base.comm_ok and not self.base.fault_latched and self._neutral(now)):
                    return False, 'fault_clear_requires_healthy_base_and_neutral_input'
            self._transition('STANDBY', 'explicit_standby')
            return True, self.reason
        if self.mode == 'FAULT':
            return False, 'clear_fault_to_standby_first'
        state = self.evaluate(now)
        if not state.base_motion_ready or not self._neutral(now):
            return False, 'manual_requires_ready_base_and_neutral_released_input'
        self._transition('MANUAL', 'explicit_manual')
        return True, self.reason
