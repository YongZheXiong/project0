import json
from pathlib import Path
import unittest

from p0_base_bridge.h60_encoder import (
    CURRENT_ENGINEERING_PROFILE,
    H60EngineeringEncoderAdapter,
    H60EngineeringEncoderProfile,
)
from p0_base_bridge.h60_protocol import MSG_TELEMETRY, PacketParser, decode_telemetry


FIXTURE = Path(__file__).parent / "fixtures" / "h60_engineering_cpr_summary.json"


def profile_mapping():
    profile = CURRENT_ENGINEERING_PROFILE
    return {
        "profile_id": profile.profile_id,
        "channel_order": list(profile.channel_order),
        "channel_wheels": list(profile.channel_wheels),
        "raw_to_forward_signs": list(profile.raw_to_forward_signs),
        "counts_per_revolution": list(profile.counts_per_revolution),
        "counter_bits": list(profile.counter_bits),
        "evidence_ids": list(profile.evidence_ids),
        "odometry_validated": profile.odometry_validated,
    }


class H60EncoderProfileTest(unittest.TestCase):
    def test_current_profile_is_strictly_valid(self):
        profile = H60EngineeringEncoderProfile.from_mapping(profile_mapping())
        profile.validate_current()

    def test_missing_extra_and_non_integer_values_are_rejected(self):
        for mutation in ("missing", "extra", "float"):
            values = profile_mapping()
            if mutation == "missing":
                del values["counter_bits"]
            elif mutation == "extra":
                values["wheel_circumference_m"] = 0.204
            else:
                values["counts_per_revolution"][0] = 2926.0
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                H60EngineeringEncoderProfile.from_mapping(values)

    def test_legacy_or_cross_coordinate_mapping_is_rejected(self):
        cases = []
        legacy = profile_mapping()
        legacy["channel_wheels"] = ["lf", "lr", "rf", "rr"]
        legacy["raw_to_forward_signs"] = [1, 1, -1, -1]
        cases.append(legacy)
        firmware_feedback = profile_mapping()
        firmware_feedback["raw_to_forward_signs"] = [-1, -1, -1, -1]
        cases.append(firmware_feedback)
        host_targets = profile_mapping()
        host_targets["raw_to_forward_signs"] = [-1, 1, -1, 1]
        cases.append(host_targets)
        for values in cases:
            with self.subTest(values=values), self.assertRaises(ValueError):
                H60EngineeringEncoderProfile.from_mapping(values).validate_current()

    def test_profile_cannot_claim_odometry_validation(self):
        values = profile_mapping()
        values["odometry_validated"] = True
        with self.assertRaises(ValueError):
            H60EngineeringEncoderProfile.from_mapping(values).validate_current()


class H60EncoderAdapterTest(unittest.TestCase):
    def test_mixed_width_wrap_normalizes_forward(self):
        adapter = H60EngineeringEncoderAdapter()
        first = adapter.update((2**31 - 5, 4, -4, 5))
        self.assertFalse(first.ready)
        reading = adapter.update((-2**31 + 5, 65530, 6, 65531))
        self.assertTrue(reading.ready)
        self.assertEqual(reading.raw_delta_counts, (10, -10, 10, -10))
        self.assertEqual(reading.forward_delta_counts, (10, 10, 10, 10))
        self.assertEqual(reading.forward_total_counts.rf, 10)
        self.assertEqual(reading.forward_total_counts.lf, 10)
        self.assertEqual(reading.forward_total_counts.rr, 10)
        self.assertEqual(reading.forward_total_counts.lr, 10)

    def test_invalid_sample_does_not_advance_state(self):
        adapter = H60EngineeringEncoderAdapter()
        adapter.update((0, 0, 0, 0))
        with self.assertRaises(ValueError):
            adapter.update((1, 32768, 1, 0))  # MB is exactly half-range.
        reading = adapter.update((1, 65535, 1, 65535))
        self.assertEqual(reading.raw_delta_counts, (1, -1, 1, -1))

    def test_h60_telemetry_ranges_are_enforced(self):
        adapter = H60EngineeringEncoderAdapter()
        for sample in ((0, -1, 0, 0), (2**31, 0, 0, 0), (0, 0, 0, 65536)):
            with self.subTest(sample=sample), self.assertRaises(ValueError):
                adapter.update(sample)

    def test_retained_real_cpr_summaries_transform_to_forward_revolutions(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(fixture["profile_id"], CURRENT_ENGINEERING_PROFILE.profile_id)
        index_by_channel = {name: i for i, name in enumerate(("MA", "MB", "MC", "MD"))}
        cpr_by_channel = dict(
            zip(
                CURRENT_ENGINEERING_PROFILE.channel_order,
                CURRENT_ENGINEERING_PROFILE.counts_per_revolution,
            )
        )
        for attempt in fixture["attempts"]:
            first_packets = PacketParser().feed(bytes.fromhex(attempt["first_packet_hex"]))
            last_packets = PacketParser().feed(bytes.fromhex(attempt["last_packet_hex"]))
            self.assertEqual(len(first_packets), 1)
            self.assertEqual(len(last_packets), 1)
            self.assertEqual(first_packets[0].message_type, MSG_TELEMETRY)
            self.assertEqual(last_packets[0].message_type, MSG_TELEMETRY)
            start = decode_telemetry(first_packets[0]).encoder_count
            end = decode_telemetry(last_packets[0]).encoder_count
            self.assertEqual(list(start), attempt["start"])
            self.assertEqual(list(end), attempt["end"])
            adapter = H60EngineeringEncoderAdapter()
            adapter.update(start)
            reading = adapter.update(end)
            index = index_by_channel[attempt["channel"]]
            self.assertEqual(
                reading.raw_delta_counts[index], attempt["expected_raw_delta"]
            )
            self.assertEqual(
                reading.forward_delta_counts[index], attempt["expected_forward_delta"]
            )
            revolutions = getattr(reading.wheel_revolutions, attempt["wheel"])
            self.assertAlmostEqual(
                revolutions,
                attempt["expected_forward_delta"] / cpr_by_channel[attempt["channel"]],
            )
            self.assertAlmostEqual(revolutions, attempt["turns"], delta=0.02)


if __name__ == "__main__":
    unittest.main()
