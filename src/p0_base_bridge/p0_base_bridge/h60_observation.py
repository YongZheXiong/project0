"""Evidence-bound read-only H60 engineering encoder observation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .h60_encoder import (
    CURRENT_ENGINEERING_PROFILE,
    H60EngineeringEncoderAdapter,
    H60EngineeringEncoderReading,
    H60WheelCounts,
    H60WheelValues,
)
from .h60_protocol import Telemetry


@dataclass(frozen=True)
class H60EngineeringEncoderStatus:
    ready: bool
    profile_id: str
    forward_total_counts: H60WheelCounts
    wheel_revolutions: H60WheelValues


class H60EngineeringEncoderObservation:
    """Track relative engineering counts without creating odometry evidence."""

    def __init__(self) -> None:
        self._adapter = H60EngineeringEncoderAdapter()
        self._latest: Optional[H60EngineeringEncoderReading] = None

    @property
    def profile_id(self) -> str:
        return CURRENT_ENGINEERING_PROFILE.profile_id

    @property
    def latest(self) -> Optional[H60EngineeringEncoderReading]:
        return self._latest

    def reset(self) -> None:
        self._adapter.reset()
        self._latest = None

    def status(self, fresh: bool) -> H60EngineeringEncoderStatus:
        reading = self._latest
        if not fresh or reading is None or not reading.ready:
            return H60EngineeringEncoderStatus(
                ready=False,
                profile_id=self.profile_id,
                forward_total_counts=H60WheelCounts(0, 0, 0, 0),
                wheel_revolutions=H60WheelValues(0.0, 0.0, 0.0, 0.0),
            )
        return H60EngineeringEncoderStatus(
            ready=True,
            profile_id=self.profile_id,
            forward_total_counts=reading.forward_total_counts,
            wheel_revolutions=reading.wheel_revolutions,
        )

    def observe(self, telemetry: Telemetry) -> H60EngineeringEncoderReading:
        try:
            reading = self._adapter.update(telemetry.encoder_count)
        except (TypeError, ValueError):
            self.reset()
            raise
        self._latest = reading
        return reading
