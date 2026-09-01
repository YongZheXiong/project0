import unittest

from p0_safety_manager.core import CommandArbiter, MotionInput


def make_arbiter(autonomy_enabled=True):
    arbiter = CommandArbiter(
        manual_timeout_sec=0.25,
        autonomy_timeout_sec=0.25,
        manual_release_hold_sec=0.50,
        autonomy_enabled=autonomy_enabled,
    )
    arbiter.update_base_state(comm_ok=True, motion_ready=True)
    return arbiter


class CoreTest(unittest.TestCase):
    def test_manual_has_priority_and_release_requires_new_autonomy(self):
        arbiter = make_arbiter()
        arbiter.update_autonomy(MotionInput(0.1, 0.0, True, 1.00))
        self.assertEqual(arbiter.decide(1.05).source, "autonomy")

        arbiter.update_manual(MotionInput(0.0, 0.4, True, 1.10))
        selected = arbiter.decide(1.11)
        self.assertEqual(selected.source, "manual")
        self.assertEqual(selected.angular_z_radps, 0.4)

        arbiter.update_manual(MotionInput(0.0, 0.0, False, 1.20))
        self.assertEqual(arbiter.decide(1.21).reason, "manual_release_hold")
        self.assertEqual(arbiter.decide(1.80).reason, "no_fresh_command")

        arbiter.update_autonomy(MotionInput(0.1, 0.0, True, 1.81))
        self.assertEqual(arbiter.decide(1.82).source, "autonomy")

    def test_timeout_and_default_autonomy_disabled_stop(self):
        arbiter = make_arbiter(autonomy_enabled=False)
        arbiter.update_autonomy(MotionInput(0.1, 0.0, True, 2.0))
        self.assertEqual(arbiter.decide(2.1).reason, "autonomy_disabled")

        arbiter.update_manual(MotionInput(0.1, 0.0, True, 2.0))
        self.assertFalse(arbiter.decide(2.3).active)

    def test_software_motion_lock_is_latched(self):
        arbiter = make_arbiter()
        arbiter.update_manual(MotionInput(0.1, 0.0, True, 3.0))
        arbiter.latch_motion_lock("test")
        self.assertEqual(arbiter.decide(3.1).reason, "software_motion_lock_latched")
        arbiter.clear_motion_lock()
        self.assertEqual(arbiter.decide(3.1).reason, "no_fresh_command")

    def test_base_communication_and_motion_ready_gate_motion(self):
        arbiter = make_arbiter()
        arbiter.update_manual(MotionInput(0.1, 0.0, True, 4.0))
        arbiter.update_base_state(comm_ok=False, motion_ready=False)
        self.assertEqual(
            arbiter.decide(4.1).reason, "base_communication_unavailable"
        )
        arbiter.update_base_state(comm_ok=True, motion_ready=False)
        self.assertEqual(arbiter.decide(4.1).reason, "base_motion_not_ready")


if __name__ == "__main__":
    unittest.main()
