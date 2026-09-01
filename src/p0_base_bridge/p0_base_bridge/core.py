"""ROS-independent protocol, normalization and command safety helpers."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Any, Mapping, Optional


_ENCODER_RE = re.compile(
    r"^P0_ENC LF=(?P<LF>-?\d+) LR=(?P<LR>-?\d+) "
    r"RF=(?P<RF>-?\d+) RR=(?P<RR>-?\d+)$"
)
_CONTROL_RE = re.compile(
    r"^P0_CTRL (?P<state>[A-Z_]+) MODE=(?P<mode>[A-Z_]+) "
    r"CMP=(?P<compare>\d+) ESTOP=(?P<estop>[01])$"
)
_ACK_RE = re.compile(r"^P0_ACK (?P<detail>.+)$")
_STOP_RE = re.compile(r"^P0_STOP (?P<reason>[A-Z_]+)$")
_STM32_BOOT = "P0_STM32_STAGE_D_PREP_BOOT"


@dataclass(frozen=True)
class EncoderCounts:
    lf: int
    lr: int
    rf: int
    rr: int


@dataclass(frozen=True)
class EncoderCountsPerRev:
    lf: float
    lr: float
    rf: float
    rr: float

    def __post_init__(self) -> None:
        for wheel in ("lf", "lr", "rf", "rr"):
            value = getattr(self, wheel)
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"encoder_counts_per_rev_{wheel} must be positive")


@dataclass(frozen=True)
class WheelRevolutions:
    lf: float
    lr: float
    rf: float
    rr: float


@dataclass(frozen=True)
class ParsedLine:
    kind: str
    values: Mapping[str, Any]
    raw: str


@dataclass(frozen=True)
class Stm32Command:
    wire: str
    moving: bool
    reason: str
    mode: str = "STOP"
    compare: int = 0


class SignedCounterUnwrapper:
    """Extend a wrapping signed hardware counter into a continuous integer."""

    def __init__(self, bits: int = 16) -> None:
        if bits < 2:
            raise ValueError("counter bits must be at least 2")
        self.bits = bits
        self.modulus = 1 << bits
        self.half_range = self.modulus >> 1
        self.minimum = -self.half_range
        self.maximum = self.half_range - 1
        self.reset()

    def reset(self) -> None:
        self._previous: Optional[int] = None
        self._total = 0

    def update(self, value: int) -> int:
        if value < self.minimum or value > self.maximum:
            raise ValueError(
                f"counter value {value} outside signed {self.bits}-bit range"
            )
        if self._previous is None:
            self._previous = value
            self._total = value
            return self._total

        delta = value - self._previous
        if delta > self.half_range:
            delta -= self.modulus
        elif delta < -self.half_range:
            delta += self.modulus
        self._total += delta
        self._previous = value
        return self._total


class EncoderCountsUnwrapper:
    """Continuously unwrap all four STM32 signed 16-bit encoder counters."""

    def __init__(self, bits: int = 16) -> None:
        self._counters = {
            wheel: SignedCounterUnwrapper(bits) for wheel in ("lf", "lr", "rf", "rr")
        }

    def reset(self) -> None:
        for counter in self._counters.values():
            counter.reset()

    def update(self, raw: EncoderCounts) -> EncoderCounts:
        return EncoderCounts(
            **{
                wheel: self._counters[wheel].update(getattr(raw, wheel))
                for wheel in ("lf", "lr", "rf", "rr")
            }
        )


def communication_is_fresh(
    serial_connected: bool, rx_age_sec: float, timeout_sec: float
) -> bool:
    """Return whether parsed STM32 traffic is within the configured deadline."""

    if not math.isfinite(timeout_sec) or timeout_sec <= 0.0:
        raise ValueError("comm_timeout_sec must be positive and finite")
    return serial_connected and math.isfinite(rx_age_sec) and rx_age_sec < timeout_sec


def normalize_encoder_counts(raw: EncoderCounts) -> EncoderCounts:
    """Return the Project0 forward-positive encoder convention.

    Stage-D measurements established that both right-side raw counters have the
    opposite sign to the corresponding physical wheel direction.
    """

    return EncoderCounts(lf=raw.lf, lr=raw.lr, rf=-raw.rf, rr=-raw.rr)


def encoder_counts_to_revolutions(
    normalized: EncoderCounts, counts_per_rev: EncoderCountsPerRev
) -> WheelRevolutions:
    """Convert forward-positive cumulative counts to per-wheel revolutions."""

    return WheelRevolutions(
        lf=normalized.lf / counts_per_rev.lf,
        lr=normalized.lr / counts_per_rev.lr,
        rf=normalized.rf / counts_per_rev.rf,
        rr=normalized.rr / counts_per_rev.rr,
    )


def parse_stm32_line(line: str) -> Optional[ParsedLine]:
    """Parse one complete STM32 status line; return None for unknown text."""

    raw = line.strip()
    match = _ENCODER_RE.fullmatch(raw)
    if match:
        values = {name.lower(): int(value) for name, value in match.groupdict().items()}
        return ParsedLine("encoder", values, raw)

    match = _CONTROL_RE.fullmatch(raw)
    if match:
        values = match.groupdict()
        return ParsedLine(
            "control",
            {
                "state": values["state"],
                "mode": values["mode"],
                "compare": int(values["compare"]),
                "estop": values["estop"] == "1",
            },
            raw,
        )

    match = _ACK_RE.fullmatch(raw)
    if match:
        return ParsedLine("ack", match.groupdict(), raw)

    match = _STOP_RE.fullmatch(raw)
    if match:
        return ParsedLine("stop", match.groupdict(), raw)

    if raw == "P0_STM32_UART_OK":
        return ParsedLine("heartbeat", {}, raw)
    if raw == "P0_STM32_RX_OK":
        return ParsedLine("rx_ack", {}, raw)
    if raw == _STM32_BOOT:
        return ParsedLine("boot", {}, raw)
    return None


def _scaled_compare(magnitude: float, full_scale: float, minimum: int, maximum: int) -> int:
    if full_scale <= 0.0:
        raise ValueError("full_scale must be positive")
    if minimum < 1 or maximum < minimum:
        raise ValueError("invalid compare limits")
    ratio = min(abs(magnitude) / full_scale, 1.0)
    return max(minimum, min(maximum, int(round(ratio * maximum))))


def command_from_velocity(
    linear_x_mps: float,
    angular_z_radps: float,
    active: bool,
    *,
    linear_deadband_mps: float,
    angular_deadband_radps: float,
    linear_full_scale_mps: float,
    angular_full_scale_radps: float,
    minimum_compare: int,
    maximum_compare: int,
) -> Stm32Command:
    """Convert a safe cardinal velocity intent to the current STM32 protocol.

    The stage-D firmware cannot represent simultaneous non-zero linear and
    angular velocity. Such mixed requests are rejected with STOP.
    """

    if not active:
        return Stm32Command("P0_CMD STOP", False, "inactive")

    linear_active = abs(linear_x_mps) > linear_deadband_mps
    angular_active = abs(angular_z_radps) > angular_deadband_radps

    if not linear_active and not angular_active:
        return Stm32Command("P0_CMD STOP", False, "neutral")
    if linear_active and angular_active:
        return Stm32Command("P0_CMD STOP", False, "unsupported_mixed_velocity")

    if linear_active:
        mode = "FWD" if linear_x_mps > 0.0 else "REV"
        compare = _scaled_compare(
            linear_x_mps, linear_full_scale_mps, minimum_compare, maximum_compare
        )
    else:
        mode = "LEFT" if angular_z_radps > 0.0 else "RIGHT"
        compare = _scaled_compare(
            angular_z_radps, angular_full_scale_radps, minimum_compare, maximum_compare
        )

    return Stm32Command(
        f"P0_CMD DRIVE {mode} {compare}", True, "drive", mode, compare
    )
