import struct
import unittest

from p0_manual_control.core import (
    JoyMapping,
    ProgressHeartbeat,
    decode_linux_joy_event,
    map_joy,
)


def mapping(confirmed=True):
    return JoyMapping(
        mapping_confirmed=confirmed,
        linear_axis=1,
        angular_axis=2,
        deadman_button=4,
        linear_scale=-0.20,
        angular_scale=0.80,
        deadzone=0.10,
    )


class CoreTest(unittest.TestCase):
    def test_unconfirmed_mapping_is_inactive(self):
        result = map_joy([0.0, -1.0, 0.5], [0, 0, 0, 0, 1], mapping(False))
        self.assertFalse(result.active)
        self.assertEqual(result.reason, "mapping_unconfirmed")

    def test_deadman_is_required(self):
        result = map_joy([0.0, -1.0, 0.5], [0, 0, 0, 0, 0], mapping())
        self.assertFalse(result.active)
        self.assertEqual(result.reason, "deadman_released")

    def test_confirmed_mapping_scales_axes(self):
        result = map_joy([0.0, -1.0, 0.5], [0, 0, 0, 0, 1], mapping())
        self.assertTrue(result.active)
        self.assertEqual(result.linear_x_mps, 0.20)
        self.assertEqual(result.angular_z_radps, 0.40)

    def test_invalid_indices_stop(self):
        result = map_joy([], [1], mapping())
        self.assertFalse(result.active)

    def test_linux_joystick_event_decoder(self):
        axis = decode_linux_joy_event(struct.pack("IhBB", 10, -32767, 0x82, 1))
        self.assertEqual(axis.kind, "axis")
        self.assertEqual(axis.number, 1)
        self.assertEqual(axis.value, -1.0)
        self.assertTrue(axis.initial)

        button = decode_linux_joy_event(struct.pack("IhBB", 20, 1, 0x01, 6))
        self.assertEqual(button.kind, "button")
        self.assertEqual(button.number, 6)
        self.assertEqual(button.value, 1.0)
        self.assertFalse(button.initial)

    def test_usb_progress_heartbeat_requires_progress_and_times_out(self):
        heartbeat = ProgressHeartbeat()
        self.assertFalse(heartbeat.observe(100, 1.00, 0.30))
        self.assertTrue(heartbeat.observe(101, 1.05, 0.30))
        self.assertTrue(heartbeat.observe(101, 1.30, 0.30))
        self.assertFalse(heartbeat.observe(101, 1.36, 0.30))
        self.assertTrue(heartbeat.observe(102, 1.40, 0.30))


if __name__ == "__main__":
    unittest.main()
