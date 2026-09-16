"""H60 engineering encoder adaptation without odometry or motion enablement.

The profile in this module is intentionally limited to the channel identity,
raw-count sign, counter width and engineering CPR evidence frozen by P2-E160.
Wheel geometry is absent by design, so this module cannot produce distance,
velocity or an odometry-ready calibration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Sequence


CHANNEL_ORDER = ("MA", "MB", "MC", "MD")
CURRENT_PROFILE_ID = "p2-e160-h60-engineering-cpr-v1"
CURRENT_CHANNEL_WHEELS = ("rf", "lf", "rr", "lr")
CURRENT_FORWARD_SIGNS = (1, -1, 1, -1)
CURRENT_COUNTS_PER_REVOLUTION = (2926, 2923, 2929, 2922)
CURRENT_COUNTER_BITS = (32, 16, 32, 16)
CURRENT_EVIDENCE_IDS = ("P2-E115", "P2-E129", "P2-E160")

_PROFILE_KEYS = {
    "profile_id",
    "channel_order",
    "channel_wheels",
    "raw_to_forward_signs",
    "counts_per_revolution",
    "counter_bits",
    "evidence_ids",
    "odometry_validated",
}


def _strict_int_tuple(values: object, name: str, length: int) -> tuple[int, ...]:
    if not isinstance(values, (list, tuple)) or len(values) != length:
        raise ValueError(f"{name} must contain exactly {length} values")
    if any(type(value) is not int for value in values):
        raise ValueError(f"{name} must contain integers")
    return tuple(values)


def _strict_str_tuple(values: object, name: str, length: int) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)) or len(values) != length:
        raise ValueError(f"{name} must contain exactly {length} values")
    if any(type(value) is not str or not value for value in values):
        raise ValueError(f"{name} must contain non-empty strings")
    return tuple(values)


@dataclass(frozen=True)
class H60EngineeringEncoderProfile:
    """Strict, evidence-bound engineering CPR profile for H60 A-D telemetry."""

    profile_id: str
    channel_order: tuple[str, str, str, str]
    channel_wheels: tuple[str, str, str, str]
    raw_to_forward_signs: tuple[int, int, int, int]
    counts_per_revolution: tuple[int, int, int, int]
    counter_bits: tuple[int, int, int, int]
    evidence_ids: tuple[str, ...]
    odometry_validated: bool = False

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> "H60EngineeringEncoderProfile":
        keys = set(values)
        missing = sorted(_PROFILE_KEYS - keys)
        extra = sorted(keys - _PROFILE_KEYS)
        if missing or extra:
            raise ValueError(f"profile keys mismatch; missing={missing}, extra={extra}")
        if type(values["profile_id"]) is not str:
            raise ValueError("profile_id must be a string")
        if type(values["odometry_validated"]) is not bool:
            raise ValueError("odometry_validated must be a boolean")
        evidence = values["evidence_ids"]
        if not isinstance(evidence, (list, tuple)) or not evidence:
            raise ValueError("evidence_ids must not be empty")
        if any(type(value) is not str or not value for value in evidence):
            raise ValueError("evidence_ids must contain non-empty strings")
        profile = cls(
            profile_id=values["profile_id"],
            channel_order=_strict_str_tuple(values["channel_order"], "channel_order", 4),
            channel_wheels=_strict_str_tuple(
                values["channel_wheels"], "channel_wheels", 4
            ),
            raw_to_forward_signs=_strict_int_tuple(
                values["raw_to_forward_signs"], "raw_to_forward_signs", 4
            ),
            counts_per_revolution=_strict_int_tuple(
                values["counts_per_revolution"], "counts_per_revolution", 4
            ),
            counter_bits=_strict_int_tuple(values["counter_bits"], "counter_bits", 4),
            evidence_ids=tuple(evidence),
            odometry_validated=values["odometry_validated"],
        )
        profile.validate_current()
        return profile

    def validate_current(self) -> None:
        expected = {
            "profile_id": CURRENT_PROFILE_ID,
            "channel_order": CHANNEL_ORDER,
            "channel_wheels": CURRENT_CHANNEL_WHEELS,
            "raw_to_forward_signs": CURRENT_FORWARD_SIGNS,
            "counts_per_revolution": CURRENT_COUNTS_PER_REVOLUTION,
            "counter_bits": CURRENT_COUNTER_BITS,
            "evidence_ids": CURRENT_EVIDENCE_IDS,
        }
        for name, value in expected.items():
            if getattr(self, name) != value:
                raise ValueError(f"{name} does not match the P2-E160 H60 profile")
        if self.odometry_validated:
            raise ValueError("P2-E160 is engineering CPR only, not odometry calibration")


CURRENT_ENGINEERING_PROFILE = H60EngineeringEncoderProfile(
    profile_id=CURRENT_PROFILE_ID,
    channel_order=CHANNEL_ORDER,
    channel_wheels=CURRENT_CHANNEL_WHEELS,
    raw_to_forward_signs=CURRENT_FORWARD_SIGNS,
    counts_per_revolution=CURRENT_COUNTS_PER_REVOLUTION,
    counter_bits=CURRENT_COUNTER_BITS,
    evidence_ids=CURRENT_EVIDENCE_IDS,
)
CURRENT_ENGINEERING_PROFILE.validate_current()


@dataclass(frozen=True)
class H60WheelCounts:
    lf: int
    lr: int
    rf: int
    rr: int


@dataclass(frozen=True)
class H60WheelValues:
    lf: float
    lr: float
    rf: float
    rr: float


@dataclass(frozen=True)
class H60EngineeringEncoderReading:
    ready: bool
    raw_delta_counts: tuple[int, int, int, int]
    forward_delta_counts: tuple[int, int, int, int]
    forward_total_counts: H60WheelCounts
    wheel_revolutions: H60WheelValues


def _zero_reading() -> H60EngineeringEncoderReading:
    zero_counts = H60WheelCounts(0, 0, 0, 0)
    zero_values = H60WheelValues(0.0, 0.0, 0.0, 0.0)
    return H60EngineeringEncoderReading(
        False, (0, 0, 0, 0), (0, 0, 0, 0), zero_counts, zero_values
    )


class H60EngineeringEncoderAdapter:
    """Unwrap H60 mixed-width counters into forward-positive wheel revolutions."""

    def __init__(
        self, profile: H60EngineeringEncoderProfile = CURRENT_ENGINEERING_PROFILE
    ) -> None:
        profile.validate_current()
        self.profile = profile
        self.reset()

    def reset(self) -> None:
        self._previous: Optional[tuple[int, int, int, int]] = None
        self._forward_totals = [0, 0, 0, 0]

    def update(self, raw_counts: Sequence[int]) -> H60EngineeringEncoderReading:
        values = _strict_int_tuple(raw_counts, "raw_counts", 4)
        for value, bits, channel in zip(
            values, self.profile.counter_bits, self.profile.channel_order
        ):
            minimum = -(1 << 31) if bits == 32 else 0
            maximum = (1 << 31) - 1 if bits == 32 else (1 << bits) - 1
            if value < minimum or value > maximum:
                raise ValueError(f"{channel} count outside H60 {bits}-bit telemetry range")

        if self._previous is None:
            self._previous = values  # Establish a zero-relative observation baseline.
            return _zero_reading()

        raw_deltas = []
        for value, previous, bits, channel in zip(
            values,
            self._previous,
            self.profile.counter_bits,
            self.profile.channel_order,
        ):
            modulus = 1 << bits
            half_range = modulus >> 1
            delta = ((value & (modulus - 1)) - (previous & (modulus - 1))) & (
                modulus - 1
            )
            if delta == half_range:
                raise ValueError(f"{channel} delta is exactly half-range and ambiguous")
            if delta > half_range:
                delta -= modulus
            raw_deltas.append(delta)

        forward_deltas = tuple(
            delta * sign
            for delta, sign in zip(raw_deltas, self.profile.raw_to_forward_signs)
        )
        next_totals = [
            total + delta for total, delta in zip(self._forward_totals, forward_deltas)
        ]

        counts_by_wheel = dict(zip(self.profile.channel_wheels, next_totals))
        revolutions_by_wheel = {
            wheel: total / cpr
            for wheel, total, cpr in zip(
                self.profile.channel_wheels,
                next_totals,
                self.profile.counts_per_revolution,
            )
        }
        self._previous = values
        self._forward_totals = next_totals
        return H60EngineeringEncoderReading(
            ready=True,
            raw_delta_counts=tuple(raw_deltas),
            forward_delta_counts=forward_deltas,
            forward_total_counts=H60WheelCounts(
                lf=counts_by_wheel["lf"],
                lr=counts_by_wheel["lr"],
                rf=counts_by_wheel["rf"],
                rr=counts_by_wheel["rr"],
            ),
            wheel_revolutions=H60WheelValues(
                lf=revolutions_by_wheel["lf"],
                lr=revolutions_by_wheel["lr"],
                rf=revolutions_by_wheel["rf"],
                rr=revolutions_by_wheel["rr"],
            ),
        )
