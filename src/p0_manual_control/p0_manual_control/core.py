"""ROS-independent gamepad mapping helpers."""

from __future__ import annotations

from dataclasses import dataclass
import struct
from typing import Optional, Sequence


JS_EVENT_BUTTON = 0x01
JS_EVENT_AXIS = 0x02
JS_EVENT_INIT = 0x80
JS_EVENT_STRUCT = struct.Struct("IhBB")


@dataclass(frozen=True)
class JoyMapping:
    mapping_confirmed: bool
    linear_axis: int
    angular_axis: int
    deadman_button: int
    linear_scale: float
    angular_scale: float
    deadzone: float


@dataclass(frozen=True)
class ManualIntent:
    linear_x_mps: float
    angular_z_radps: float
    active: bool
    reason: str


@dataclass(frozen=True)
class LinuxJoyEvent:
    kind: str
    number: int
    value: float
    initial: bool


@dataclass
class ProgressHeartbeat:
    """Treat a monotonically changing counter as a link heartbeat."""

    last_count: Optional[int] = None
    last_progress_time: float = 0.0
    progress_seen: bool = False

    def observe(self, count: int, now: float, timeout_sec: float) -> bool:
        if self.last_count is None:
            self.last_count = count
            self.last_progress_time = now
            return False
        if count != self.last_count:
            self.last_count = count
            self.last_progress_time = now
            self.progress_seen = True
        return self.progress_seen and now - self.last_progress_time <= timeout_sec


def decode_linux_joy_event(data: bytes) -> LinuxJoyEvent:
    """Decode one Linux joystick API event from /dev/input/js*.

    The event layout is stable Linux userspace ABI: uint32 time, int16 value,
    uint8 type and uint8 number.
    """

    if len(data) != JS_EVENT_STRUCT.size:
        raise ValueError("Linux joystick events must contain exactly 8 bytes")
    _, raw_value, event_type, number = JS_EVENT_STRUCT.unpack(data)
    initial = bool(event_type & JS_EVENT_INIT)
    base_type = event_type & ~JS_EVENT_INIT
    if base_type == JS_EVENT_AXIS:
        value = max(-1.0, min(1.0, raw_value / 32767.0))
        return LinuxJoyEvent("axis", number, value, initial)
    if base_type == JS_EVENT_BUTTON:
        return LinuxJoyEvent("button", number, float(raw_value != 0), initial)
    return LinuxJoyEvent("unknown", number, float(raw_value), initial)


def _axis(axes: Sequence[float], index: int, deadzone: float) -> float:
    if index < 0 or index >= len(axes):
        raise IndexError("axis index unavailable")
    value = float(axes[index])
    return 0.0 if abs(value) <= deadzone else value


def map_joy(
    axes: Sequence[float], buttons: Sequence[int], mapping: JoyMapping
) -> ManualIntent:
    if not mapping.mapping_confirmed:
        return ManualIntent(0.0, 0.0, False, "mapping_unconfirmed")
    if mapping.deadman_button < 0 or mapping.deadman_button >= len(buttons):
        return ManualIntent(0.0, 0.0, False, "deadman_button_unavailable")
    if int(buttons[mapping.deadman_button]) == 0:
        return ManualIntent(0.0, 0.0, False, "deadman_released")
    try:
        linear = _axis(axes, mapping.linear_axis, mapping.deadzone)
        angular = _axis(axes, mapping.angular_axis, mapping.deadzone)
    except IndexError:
        return ManualIntent(0.0, 0.0, False, "axis_unavailable")
    return ManualIntent(
        linear * mapping.linear_scale,
        angular * mapping.angular_scale,
        True,
        "deadman_active",
    )
