import unittest

from no_orin_web_teleop.controller import ControllerConfig, WebTeleopController
from no_orin_web_teleop.fake_serial import FakeH60Serial
from p0_base_bridge.h60_protocol import MSG_M2A_CALIBRATION_HOLD, PacketParser


class ControllerTests(unittest.TestCase):
    def make_controller(self, *, lease_ms=100, loop_gap_ms=500, defer_arm=False, field_auto_stop_ms=None):
        link = FakeH60Serial()
        controller = WebTeleopController(
            link,
            config=ControllerConfig(
                command_lease_ms=lease_ms,
                max_loop_gap_ms=loop_gap_ms,
                defer_arm_until_motion=defer_arm,
                field_auto_stop_ms=field_auto_stop_ms,
            ),
        )
        return controller, link

    def test_rejects_unknown_intent_without_fake_serial_command(self):
        controller, link = self.make_controller()
        result = controller.handle_intent("PWM_SLIDER", now_ms=0, sequence=1)

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "unknown_intent")
        self.assertEqual(link.commands, [])

    def test_requires_arm_before_forward_profile(self):
        controller, link = self.make_controller()
        result = controller.handle_intent("FORWARD_LOW", now_ms=0, sequence=1)

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "not_armed")
        self.assertEqual(link.commands, [])

    def test_real_w2_pending_arm_does_not_arm_until_same_client_holds_direction(self):
        controller, link = self.make_controller(defer_arm=True)
        pending = controller.handle_intent(
            "ARM_REQUEST", now_ms=0, client_id="operator", sequence=1
        )
        self.assertEqual((pending.state, pending.reason), ("ARM_PENDING", "arm_pending"))
        self.assertEqual(link.commands, [])
        wrong = controller.handle_intent(
            "FORWARD_LOW", now_ms=3000, client_id="other", sequence=1
        )
        self.assertEqual(wrong.reason, "arm_client_mismatch")
        self.assertEqual(link.commands, [])
        first = controller.handle_intent(
            "FORWARD_LOW", now_ms=3001, client_id="operator", sequence=2
        )
        self.assertTrue(first.accepted)
        self.assertEqual(
            [item["command"] for item in link.commands],
            ["ARM", "PROFILE_FORWARD_LOW"],
        )

    def test_pending_arm_stop_disconnect_and_expiry_never_send_arm(self):
        for action in ("stop", "disconnect", "expiry"):
            with self.subTest(action=action):
                controller, link = self.make_controller(defer_arm=True)
                controller.handle_intent(
                    "ARM_REQUEST", now_ms=0, client_id="operator", sequence=1
                )
                if action == "stop":
                    controller.handle_intent("STOP", now_ms=100, client_id="operator", sequence=2)
                elif action == "disconnect":
                    controller.client_disconnect(client_id="operator", now_ms=100)
                else:
                    controller.tick(now_ms=5000)
                result = controller.handle_intent(
                    "FORWARD_LOW", now_ms=5001, client_id="operator", sequence=3
                )
                self.assertFalse(result.accepted)
                self.assertEqual(result.reason,
                                 "client_session_closed" if action == "disconnect" else "not_armed")
                self.assertNotIn("ARM", [item["command"] for item in link.commands])

    def test_forward_hold_renews_lease_then_expiry_forces_stop(self):
        controller, link = self.make_controller(lease_ms=100, loop_gap_ms=1000)

        self.assertTrue(
            controller.handle_intent("ARM_REQUEST", now_ms=0, sequence=1).accepted
        )
        first = controller.handle_intent("FORWARD_LOW", now_ms=10, sequence=2)
        second = controller.handle_intent("FORWARD_LOW", now_ms=80, sequence=3)
        tick = controller.tick(now_ms=181)

        self.assertTrue(first.accepted)
        self.assertTrue(second.accepted)
        first_profile = [
            item for item in link.commands
            if item["command"] == "PROFILE_FORWARD_LOW"
        ][0]
        packets = PacketParser().feed(bytes.fromhex(first_profile["frame_hex"]))
        self.assertEqual(len(packets), 1)
        self.assertEqual(packets[0].message_type, MSG_M2A_CALIBRATION_HOLD)
        self.assertEqual(packets[0].payload, b"\xf0\x01\x50\x00")
        self.assertEqual(tick.reason, "lease_expired_stop")
        self.assertEqual(controller.active_direction, None)
        self.assertEqual(link.commands[-1]["command"], "STOP")

    def test_field_auto_stop_precedes_hard_link_limit_and_requires_new_arm(self):
        controller, link = self.make_controller(
            lease_ms=220, loop_gap_ms=1000, defer_arm=True, field_auto_stop_ms=350
        )
        controller.handle_intent("ARM_REQUEST", now_ms=0, sequence=1)
        controller.handle_intent("FORWARD_LOW", now_ms=10, sequence=2)
        controller.handle_intent("FORWARD_LOW", now_ms=200, sequence=3)
        stopped = controller.tick(now_ms=360)
        rejected = controller.handle_intent("FORWARD_LOW", now_ms=375, sequence=4)

        self.assertEqual(stopped.reason, "field_auto_stop")
        self.assertEqual(stopped.state, "DISARMED")
        self.assertIsNone(stopped.fault_reason)
        self.assertEqual(link.commands[-1]["command"], "STOP")
        self.assertEqual(link.commands[-1]["reason"], "field_auto_stop")
        self.assertEqual(rejected.reason, "not_armed")
        self.assertEqual(
            [item["command"] for item in link.commands].count("PROFILE_FORWARD_LOW"), 2
        )

    def test_delayed_field_renewal_stops_before_another_profile(self):
        controller, link = self.make_controller(
            lease_ms=1000, loop_gap_ms=1000, defer_arm=True, field_auto_stop_ms=350
        )
        controller.handle_intent("ARM_REQUEST", now_ms=0, sequence=1)
        controller.handle_intent("FORWARD_LOW", now_ms=10, sequence=2)
        stopped = controller.handle_intent("FORWARD_LOW", now_ms=370, sequence=3)

        self.assertEqual(stopped.reason, "field_auto_stop")
        self.assertEqual(stopped.state, "DISARMED")
        self.assertEqual(
            [item["command"] for item in link.commands],
            ["ARM", "PROFILE_FORWARD_LOW", "STOP"],
        )

    def test_direction_change_requires_stop_and_rearm(self):
        controller, link = self.make_controller()
        controller.handle_intent("ARM_REQUEST", now_ms=0, sequence=1)
        controller.handle_intent("FORWARD_LOW", now_ms=10, sequence=2)
        result = controller.handle_intent("REVERSE_LOW", now_ms=20, sequence=3)

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "direction_change_requires_neutral")
        self.assertEqual(result.state, "DISARMED")
        self.assertEqual(link.commands[-1]["command"], "STOP")

    def test_disconnect_forces_stop_and_disarm(self):
        controller, link = self.make_controller()
        controller.handle_intent("ARM_REQUEST", now_ms=0, sequence=1)
        controller.handle_intent("REVERSE_LOW", now_ms=10, sequence=2)

        result = controller.client_disconnect(client_id="browser", now_ms=20)

        self.assertTrue(result.accepted)
        self.assertEqual(result.reason, "disconnect_stop_disarm")
        self.assertEqual([item["command"] for item in link.commands[-2:]], ["STOP", "DISARM"])
        self.assertIsNone(controller.active_direction)

    def test_disconnect_rejects_old_page_even_after_new_sequence(self):
        controller, link = self.make_controller(defer_arm=True)
        controller.handle_intent("ARM_REQUEST", now_ms=0, client_id="old", sequence=1)
        controller.client_disconnect(client_id="old", now_ms=10)
        old = controller.handle_intent("ARM_REQUEST", now_ms=20, client_id="old", sequence=99)
        fresh = controller.handle_intent("ARM_REQUEST", now_ms=21, client_id="new", sequence=1)
        self.assertEqual((old.accepted, old.reason), (False, "client_session_closed"))
        self.assertEqual((fresh.accepted, fresh.reason), (True, "arm_pending"))
        self.assertNotIn("ARM", [item["command"] for item in link.commands])

    def test_lost_disconnect_notification_expires_lease_and_rejects_queued_old_intents(self):
        controller, link = self.make_controller(lease_ms=100, loop_gap_ms=1000, defer_arm=True)
        controller.handle_intent("ARM_REQUEST", now_ms=0, client_id="old", sequence=1)
        controller.handle_intent("FORWARD_LOW", now_ms=10, client_id="old", sequence=2)
        stopped = controller.tick(now_ms=111)
        old = controller.handle_intent("ARM_REQUEST", now_ms=112, client_id="old", sequence=99)
        self.assertEqual(stopped.reason, "lease_expired_stop")
        self.assertEqual((old.accepted, old.reason), (False, "client_session_closed"))
        self.assertEqual([item["command"] for item in link.commands],
                         ["ARM", "PROFILE_FORWARD_LOW", "STOP"])

    def test_late_queued_profile_cannot_bypass_lease_before_watchdog_tick(self):
        controller, link = self.make_controller(lease_ms=100, loop_gap_ms=1000, defer_arm=True)
        controller.handle_intent("ARM_REQUEST", now_ms=0, client_id="old", sequence=1)
        controller.handle_intent("FORWARD_LOW", now_ms=10, client_id="old", sequence=2)
        late = controller.handle_intent("FORWARD_LOW", now_ms=111, client_id="old", sequence=3)
        self.assertFalse(late.accepted)
        self.assertEqual(late.reason, "client_session_closed")
        self.assertEqual([item["command"] for item in link.commands],
                         ["ARM", "PROFILE_FORWARD_LOW", "STOP"])

    def test_unconfirmed_disconnect_stop_latches_fault_after_link_recovers(self):
        controller, link = self.make_controller(lease_ms=1000, loop_gap_ms=1000)
        controller.handle_intent("ARM_REQUEST", now_ms=0, client_id="old", sequence=1)
        controller.handle_intent("FORWARD_LOW", now_ms=10, client_id="old", sequence=2)
        link.set_scenario("timeout")
        lost = controller.client_disconnect(client_id="old", now_ms=20)
        self.assertEqual((lost.accepted, lost.state), (False, "FAULT"))
        self.assertEqual(lost.reason, "telemetry_timeout")
        self.assertFalse(link.commands[-2]["ack"])
        self.assertFalse(link.commands[-1]["ack"])
        link.clear()
        stale = controller.handle_intent("ARM_REQUEST", now_ms=30, client_id="old", sequence=3)
        self.assertEqual(stale.reason, "client_session_closed")
        self.assertNotIn("ARM", [item["command"] for item in link.commands[2:]])

    def test_unconfirmed_expiry_stop_never_reports_disarmed_success(self):
        controller, link = self.make_controller(lease_ms=100, loop_gap_ms=1000)
        controller.handle_intent("ARM_REQUEST", now_ms=0, sequence=1)
        controller.handle_intent("FORWARD_LOW", now_ms=10, sequence=2)
        link.set_scenario("timeout")
        result = controller.tick(now_ms=111)
        self.assertEqual((result.accepted, result.state), (False, "FAULT"))
        self.assertEqual(result.reason, "telemetry_timeout")

    def test_unconfirmed_disarm_cannot_clear_fault(self):
        controller, link = self.make_controller()
        link.set_scenario("timeout")
        controller.handle_intent("ARM_REQUEST", now_ms=0, sequence=1)
        result = controller.handle_intent("DISARM", now_ms=1, sequence=2)
        self.assertEqual((result.accepted, result.state), (False, "FAULT"))
        self.assertEqual(result.reason, "telemetry_timeout")

    def test_fake_fault_locks_motion_without_profile_command(self):
        controller, link = self.make_controller()
        controller.handle_intent("ARM_REQUEST", now_ms=0, sequence=1)
        controller.set_fake_scenario("fault", now_ms=5)

        result = controller.handle_intent("FORWARD_LOW", now_ms=10, sequence=2)

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "h60_fault")
        self.assertEqual(result.state, "FAULT")
        self.assertNotIn("PROFILE_FORWARD_LOW", [item["command"] for item in link.commands])

    def test_fake_identity_drift_blocks_arm(self):
        controller, _ = self.make_controller()
        controller.set_fake_scenario("identity_drift", now_ms=0)

        result = controller.handle_intent("ARM_REQUEST", now_ms=1, sequence=1)

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "identity_drift")
        self.assertEqual(result.state, "FAULT")

    def test_fake_timeout_blocks_arm(self):
        controller, _ = self.make_controller()
        controller.set_fake_scenario("timeout", now_ms=0)

        result = controller.handle_intent("ARM_REQUEST", now_ms=1, sequence=1)

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "telemetry_timeout")
        self.assertEqual(result.state, "FAULT")

    def test_fake_protocol_errors_block_motion(self):
        for scenario in ("crc_error", "length_error", "sequence_error"):
            with self.subTest(scenario=scenario):
                controller, _ = self.make_controller()
                controller.set_fake_scenario(scenario, now_ms=0)

                result = controller.handle_intent("ARM_REQUEST", now_ms=1, sequence=1)

                self.assertFalse(result.accepted)
                self.assertEqual(result.reason, scenario)
                self.assertEqual(result.state, "FAULT")

    def test_loop_lateness_forces_fault_stop(self):
        controller, link = self.make_controller(lease_ms=1000, loop_gap_ms=50)
        controller.handle_intent("ARM_REQUEST", now_ms=0, sequence=1)
        controller.handle_intent("FORWARD_LOW", now_ms=10, sequence=2)
        controller.tick(now_ms=20)

        result = controller.tick(now_ms=80)

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "backend_loop_late")
        self.assertEqual(link.commands[-1]["command"], "STOP")

    def test_fake_reboot_locks_active_motion_on_tick(self):
        controller, link = self.make_controller(lease_ms=1000, loop_gap_ms=500)
        controller.handle_intent("ARM_REQUEST", now_ms=0, sequence=1)
        controller.handle_intent("FORWARD_LOW", now_ms=10, sequence=2)
        controller.set_fake_scenario("reboot", now_ms=20)

        result = controller.tick(now_ms=21)

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "h60_reboot")
        self.assertEqual(result.state, "FAULT")
        self.assertEqual(link.commands[-1]["command"], "STOP")

    def test_stale_sequence_rejected_but_stop_is_accepted(self):
        controller, link = self.make_controller()
        controller.handle_intent("ARM_REQUEST", now_ms=0, sequence=10)
        stale = controller.handle_intent("FORWARD_LOW", now_ms=1, sequence=9)
        stop = controller.handle_intent("STOP", now_ms=2, sequence=9)

        self.assertFalse(stale.accepted)
        self.assertEqual(stale.reason, "stale_sequence")
        self.assertTrue(stop.accepted)
        self.assertEqual(link.commands[-1]["command"], "STOP")


if __name__ == "__main__":
    unittest.main()
