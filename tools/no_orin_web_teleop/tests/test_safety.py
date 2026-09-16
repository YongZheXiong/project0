import unittest

from no_orin_web_teleop.controller import WebTeleopController
from no_orin_web_teleop.fake_serial import FakeH60Serial
from no_orin_web_teleop.safety import build_safety_panel_state


class SafetyPanelTests(unittest.TestCase):
    def make_safety(self):
        controller = WebTeleopController(FakeH60Serial())
        state = controller.export_state(now_ms=0)
        return controller, build_safety_panel_state(state)

    def test_default_panel_locks_entity_actions_after_w1(self):
        _, safety = self.make_safety()

        self.assertEqual(safety["gate"], "W1.5")
        self.assertEqual(safety["overall"], "READY_FOR_W2_PACKAGE_PREP_ONLY")
        self.assertEqual(safety["mode"], "OFFLINE_FAKE_SERIAL_ONLY")
        self.assertEqual(
            safety["historical_w1"]["status"],
            "W1_REAL_COLD_PROBE_PASS / CLOSEOUT_OK",
        )
        self.assertEqual(safety["live_physical_state"], "UNCONFIRMED_IN_THIS_SESSION")
        self.assertEqual(safety["next_gate"]["status"], "LOCKED")
        self.assertIn("open_real_h60_serial", safety["prohibited_actions"])

    def test_simulated_profile_never_unlocks_w2(self):
        controller = WebTeleopController(FakeH60Serial())
        controller.handle_intent("ARM_REQUEST", now_ms=0, sequence=1)
        controller.handle_intent("FORWARD_LOW", now_ms=10, sequence=2)

        safety = build_safety_panel_state(controller.export_state(now_ms=20))

        self.assertEqual(safety["current_backend"]["simulated_profile_commands"], 1)
        self.assertEqual(safety["entity_authorization"], "LOCKED_PENDING_NEW_FIELD_PACKAGE")
        self.assertEqual(safety["next_gate"]["status"], "LOCKED")

    def test_fault_is_attention_not_entity_permission(self):
        controller = WebTeleopController(FakeH60Serial())
        controller.set_fake_scenario("identity_drift", now_ms=0)
        controller.handle_intent("ARM_REQUEST", now_ms=1, sequence=1)

        safety = build_safety_panel_state(controller.export_state(now_ms=2))

        self.assertEqual(safety["overall"], "ATTENTION_FAULT_LATCHED")
        self.assertEqual(safety["current_backend"]["fault_reason"], "identity_drift")
        self.assertIn("arm_real_h60", safety["prohibited_actions"])


if __name__ == "__main__":
    unittest.main()
