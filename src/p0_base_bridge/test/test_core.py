import os
import pty
import select
import unittest

from p0_base_bridge.core import (
    EncoderCounts,
    EncoderCountsPerRev,
    EncoderCountsUnwrapper,
    SignedCounterUnwrapper,
    command_from_velocity,
    communication_is_fresh,
    encoder_counts_to_revolutions,
    normalize_encoder_counts,
    parse_stm32_line,
)
from p0_base_bridge.serial_port import PosixSerialPort


PARAMS = dict(
    linear_deadband_mps=0.01,
    angular_deadband_radps=0.02,
    linear_full_scale_mps=0.20,
    angular_full_scale_radps=0.80,
    minimum_compare=6,
    maximum_compare=12,
)


class CoreTest(unittest.TestCase):
    def test_signed_counter_unwraps_both_directions(self):
        forward = SignedCounterUnwrapper()
        self.assertEqual(forward.update(32766), 32766)
        self.assertEqual(forward.update(32767), 32767)
        self.assertEqual(forward.update(-32768), 32768)
        self.assertEqual(forward.update(-32767), 32769)

        reverse = SignedCounterUnwrapper()
        self.assertEqual(reverse.update(-32767), -32767)
        self.assertEqual(reverse.update(-32768), -32768)
        self.assertEqual(reverse.update(32767), -32769)
        self.assertEqual(reverse.update(32766), -32770)

    def test_encoder_unwrapper_preserves_each_wheel(self):
        unwrapper = EncoderCountsUnwrapper()
        first = unwrapper.update(EncoderCounts(32767, -32768, 10, -10))
        second = unwrapper.update(EncoderCounts(-32768, 32767, 15, -15))
        self.assertEqual(first, EncoderCounts(32767, -32768, 10, -10))
        self.assertEqual(second, EncoderCounts(32768, -32769, 15, -15))
        unwrapper.reset()
        self.assertEqual(
            unwrapper.update(EncoderCounts(1, 2, 3, 4)), EncoderCounts(1, 2, 3, 4)
        )

    def test_signed_counter_rejects_out_of_range_values(self):
        counter = SignedCounterUnwrapper()
        for value in (-32769, 32768):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    counter.update(value)

    def test_communication_freshness_uses_configured_timeout(self):
        self.assertTrue(communication_is_fresh(True, 1.49, 1.50))
        self.assertFalse(communication_is_fresh(True, 1.50, 1.50))
        self.assertFalse(communication_is_fresh(False, 0.0, 1.50))
        for timeout in (0.0, -1.0, float("nan"), float("inf")):
            with self.subTest(timeout=timeout):
                with self.assertRaises(ValueError):
                    communication_is_fresh(True, 0.0, timeout)

    def test_stage_d_encoder_sign_normalization(self):
        cases = [
            (EncoderCounts(352, 331, -397, -293), EncoderCounts(352, 331, 397, 293)),
            (EncoderCounts(-315, -360, 381, 242), EncoderCounts(-315, -360, -381, -242)),
            (EncoderCounts(-355, -397, -359, -272), EncoderCounts(-355, -397, 359, 272)),
            (EncoderCounts(348, 390, 367, 308), EncoderCounts(348, 390, -367, -308)),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(normalize_encoder_counts(raw), expected)

    def test_per_wheel_encoder_counts_to_revolutions(self):
        calibration = EncoderCountsPerRev(
            lf=3367.95, lr=3090.10, rf=3179.05, rr=3047.25
        )
        normalized = EncoderCounts(336795, -309010, 317905, -304725)
        revolutions = encoder_counts_to_revolutions(normalized, calibration)
        self.assertAlmostEqual(revolutions.lf, 100.0)
        self.assertAlmostEqual(revolutions.lr, -100.0)
        self.assertAlmostEqual(revolutions.rf, 100.0)
        self.assertAlmostEqual(revolutions.rr, -100.0)

    def test_encoder_counts_per_rev_rejects_non_positive_or_non_finite(self):
        invalid_values = (0.0, -1.0, float("nan"), float("inf"))
        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    EncoderCountsPerRev(lf=value, lr=3090.10, rf=3179.05, rr=3047.25)

    def test_protocol_parser(self):
        encoder = parse_stm32_line("P0_ENC LF=1 LR=-2 RF=3 RR=-4")
        self.assertIsNotNone(encoder)
        self.assertEqual(encoder.kind, "encoder")
        self.assertEqual(encoder.values, {"lf": 1, "lr": -2, "rf": 3, "rr": -4})

        boot = parse_stm32_line("P0_STM32_STAGE_D_PREP_BOOT")
        self.assertIsNotNone(boot)
        self.assertEqual(boot.kind, "boot")

        control = parse_stm32_line("P0_CTRL SAFE MODE=STOP CMP=0 ESTOP=1")
        self.assertIsNotNone(control)
        self.assertTrue(control.values["estop"])
        self.assertEqual(control.values["compare"], 0)

        self.assertEqual(parse_stm32_line("P0_STM32_UART_OK").kind, "heartbeat")
        self.assertEqual(parse_stm32_line("P0_ACK DRIVE FWD CMP=12").kind, "ack")
        self.assertEqual(parse_stm32_line("P0_STOP TIMEOUT").kind, "stop")
        self.assertIsNone(parse_stm32_line("partial garbage"))

    def test_command_conversion_is_fail_safe(self):
        self.assertEqual(
            command_from_velocity(0.0, 0.0, False, **PARAMS).wire, "P0_CMD STOP"
        )
        self.assertEqual(
            command_from_velocity(0.0, 0.0, True, **PARAMS).wire, "P0_CMD STOP"
        )
        mixed = command_from_velocity(0.1, 0.3, True, **PARAMS)
        self.assertEqual(mixed.wire, "P0_CMD STOP")
        self.assertEqual(mixed.reason, "unsupported_mixed_velocity")

    def test_cardinal_command_conversion(self):
        cases = [
            (0.20, 0.0, "P0_CMD DRIVE FWD 12"),
            (-0.20, 0.0, "P0_CMD DRIVE REV 12"),
            (0.0, 0.80, "P0_CMD DRIVE LEFT 12"),
            (0.0, -0.80, "P0_CMD DRIVE RIGHT 12"),
            (0.02, 0.0, "P0_CMD DRIVE FWD 6"),
        ]
        for linear, angular, wire in cases:
            with self.subTest(wire=wire):
                self.assertEqual(
                    command_from_velocity(linear, angular, True, **PARAMS).wire,
                    wire,
                )

    def test_posix_serial_port_round_trip(self):
        master_fd, slave_fd = pty.openpty()
        device = os.ttyname(slave_fd)
        os.close(slave_fd)
        port = PosixSerialPort(device, 115200)
        try:
            inbound = b"\xa5\x5a\x01\x80\x00\x00\x00"
            outbound = b"\xa5\x5a\x01\x04\x00\x00\x00"
            os.write(master_fd, inbound)
            self.assertEqual(port.read(128, 0.10), inbound)
            port.write(outbound)
            readable, _, _ = select.select([master_fd], [], [], 0.10)
            self.assertEqual(readable, [master_fd])
            self.assertEqual(os.read(master_fd, 128), outbound)
        finally:
            port.close()
            os.close(master_fd)


if __name__ == "__main__":
    unittest.main()
