import unittest

from p0_base_bridge.h60_observation import H60EngineeringEncoderObservation
from p0_base_bridge.h60_protocol import STATE_DISARMED, Telemetry


def telemetry(counts):
    return Telemetry(
        state=STATE_DISARMED,
        fault=0,
        motion_output_available=False,
        self_test_ok=True,
        encoder_count=counts,
        encoder_delta=(0, 0, 0, 0),
        vin_raw=0,
        vin_nominal_mv=0,
        firmware_version=(0, 2, 8),
        boot_fault_code=0,
        capabilities=0,
        session_id=0,
        sequence=1,
    )


class H60EngineeringEncoderObservationTest(unittest.TestCase):
    def test_first_sample_is_baseline_then_forward_counts_are_published(self):
        observation = H60EngineeringEncoderObservation()

        first = observation.observe(telemetry((0, 0, 0, 0)))
        self.assertFalse(first.ready)
        reading = observation.observe(telemetry((10, 65526, 10, 65526)))

        self.assertTrue(reading.ready)
        self.assertEqual(reading.forward_total_counts.rf, 10)
        self.assertEqual(reading.forward_total_counts.lf, 10)
        self.assertEqual(reading.forward_total_counts.rr, 10)
        self.assertEqual(reading.forward_total_counts.lr, 10)
        self.assertAlmostEqual(reading.wheel_revolutions.rf, 10 / 2926)
        self.assertEqual(
            observation.profile_id,
            "p2-e160-h60-engineering-cpr-v1",
        )
        fresh = observation.status(True)
        self.assertTrue(fresh.ready)
        self.assertEqual(fresh.forward_total_counts.rf, 10)
        stale = observation.status(False)
        self.assertFalse(stale.ready)
        self.assertEqual(stale.forward_total_counts.rf, 0)
        self.assertEqual(stale.wheel_revolutions.rf, 0.0)

    def test_reset_requires_a_new_baseline(self):
        observation = H60EngineeringEncoderObservation()
        observation.observe(telemetry((0, 0, 0, 0)))
        self.assertTrue(
            observation.observe(telemetry((1, 65535, 1, 65535))).ready
        )

        observation.reset()
        self.assertIsNone(observation.latest)
        self.assertFalse(
            observation.observe(telemetry((100, 100, 100, 100))).ready
        )

    def test_invalid_sample_clears_prior_observation(self):
        observation = H60EngineeringEncoderObservation()
        observation.observe(telemetry((0, 0, 0, 0)))
        with self.assertRaises(ValueError):
            observation.observe(telemetry((0, 32768, 0, 0)))
        self.assertIsNone(observation.latest)
        self.assertFalse(observation.observe(telemetry((0, 1, 0, 0))).ready)


if __name__ == "__main__":
    unittest.main()
