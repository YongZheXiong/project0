import struct
import unittest

from p0_base_bridge.h60_protocol import (
    H60CommandPlanner,
    MAX_PAYLOAD,
    MSG_ACK,
    MSG_ARM,
    MSG_HEARTBEAT,
    MSG_NACK,
    MSG_STOP,
    MSG_TELEMETRY,
    MSG_WHEEL_TARGET,
    MotionGate,
    MotionIntent,
    Packet,
    PacketParser,
    STATE_ARMED,
    STATE_DISARMED,
    STATUS_MOTION_LOCKED,
    STATUS_OK,
    decode_command_status,
    decode_telemetry,
    differential_targets_mmps,
    encode_packet,
)


def telemetry_packet(
    *,
    session_id,
    sequence=1,
    state=STATE_DISARMED,
    fault=0,
    motion_available=True,
    self_test_ok=True,
):
    payload = struct.pack(
        "<BBBB4i4hHHBBBBI",
        state,
        fault,
        int(motion_available),
        int(self_test_ok),
        101,
        -202,
        303,
        -404,
        11,
        -12,
        13,
        -14,
        2789,
        24000,
        0,
        1,
        1,
        0,
        0x12345678,
    )
    return Packet(MSG_TELEMETRY, session_id, sequence, payload)


def response_packet(
    command_type,
    *,
    session_id,
    sequence,
    status=STATUS_OK,
    state=STATE_DISARMED,
    fault=0,
    nack=False,
):
    return Packet(
        MSG_NACK if nack else MSG_ACK,
        session_id,
        sequence,
        bytes((command_type, status, state, fault)),
    )


class CodecTest(unittest.TestCase):
    def test_known_firmware_compatible_heartbeat_vector(self):
        packet = Packet(MSG_HEARTBEAT, 0x11223344, 0x55667788)
        self.assertEqual(
            encode_packet(packet).hex(),
            "a55a0101000044332211887766554cb5b353",
        )

    def test_incremental_parser_resynchronizes_after_noise_and_bad_crc(self):
        valid = encode_packet(Packet(MSG_HEARTBEAT, 7, 9))
        corrupt = bytearray(valid)
        corrupt[-1] ^= 0x80
        parser = PacketParser()

        self.assertEqual(parser.feed(b"noise\xa5"), [])
        self.assertEqual(parser.feed(bytes(corrupt)[1:8]), [])
        packets = parser.feed(bytes(corrupt)[8:] + valid[:5])
        self.assertEqual(packets, [])
        packets = parser.feed(valid[5:])

        self.assertEqual(packets, [Packet(MSG_HEARTBEAT, 7, 9)])
        self.assertEqual(parser.stats.crc_errors, 1)
        self.assertGreaterEqual(parser.stats.discarded_bytes, 5)

    def test_parser_rejects_oversized_payload_and_recovers(self):
        malformed = b"\xa5\x5a\x01\x01" + struct.pack("<H", MAX_PAYLOAD + 1)
        parser = PacketParser()
        self.assertEqual(parser.feed(malformed), [])
        valid = encode_packet(Packet(MSG_STOP))
        self.assertEqual(parser.feed(valid), [Packet(MSG_STOP)])
        self.assertEqual(parser.stats.length_errors, 1)

    def test_parser_rejects_wrong_version_and_recovers(self):
        wrong_version = bytearray(encode_packet(Packet(MSG_STOP)))
        wrong_version[2] = 2
        parser = PacketParser()
        self.assertEqual(parser.feed(wrong_version), [])
        self.assertEqual(
            parser.feed(encode_packet(Packet(MSG_HEARTBEAT, 1, 1))),
            [Packet(MSG_HEARTBEAT, 1, 1)],
        )
        self.assertEqual(parser.stats.version_errors, 1)

    def test_telemetry_and_command_status_decode(self):
        telemetry = decode_telemetry(telemetry_packet(session_id=0x44, sequence=5))
        self.assertEqual(telemetry.encoder_count, (101, -202, 303, -404))
        self.assertEqual(telemetry.encoder_delta, (11, -12, 13, -14))
        self.assertEqual(telemetry.firmware_version, (0, 1, 1))
        self.assertEqual(telemetry.boot_fault_code, 0x12345678)
        self.assertTrue(telemetry.motion_output_available)

        status = decode_command_status(
            response_packet(
                MSG_ARM,
                session_id=0x44,
                sequence=6,
                status=STATUS_MOTION_LOCKED,
                nack=True,
            )
        )
        self.assertTrue(status.nack)
        self.assertEqual(status.status, STATUS_MOTION_LOCKED)

    def test_differential_mapping_uses_integer_mm_per_second(self):
        targets = differential_targets_mmps(
            0.20,
            1.0,
            0.10,
            ("lf", "rf", "lr", "rr"),
            (1, -1, 1, -1),
            1000,
        )
        self.assertEqual(targets, (150, -250, 150, -250))

        with self.assertRaises(ValueError):
            differential_targets_mmps(
                0.20,
                0.0,
                0.10,
                ("unmapped_a", "unmapped_b", "unmapped_c", "unmapped_d"),
                (1, 1, 1, 1),
                1000,
            )
        with self.assertRaises(ValueError):
            differential_targets_mmps(
                0.20,
                0.0,
                0.10,
                ("lf", "lr", "rf", "rr"),
                (1, 1, 1, 1),
                0,
            )

        self.assertEqual(
            differential_targets_mmps(
                0.20,
                1.0,
                0.10,
                ("lf", "rf", "lr", "rr"),
                (1, -1, 1, -1),
                200,
            ),
            (150, -200, 150, -200),
        )


class PlannerTest(unittest.TestCase):
    def make_planner(self):
        sessions = iter((0x101, 0x202, 0x303))
        return H60CommandPlanner(session_factory=lambda: next(sessions))

    @staticmethod
    def plan(planner, now_ms, intent, gate):
        return planner.plan(
            now_ms=now_ms,
            intent=intent,
            command_fresh=True,
            gate=gate,
            track_width_m=0.10,
            channel_wheels=("lf", "lr", "rf", "rr"),
            channel_signs=(1, 1, 1, 1),
            wheel_target_limit_mmps=1000,
        )

    def test_startup_and_config_gates_never_arm(self):
        planner = self.make_planner()
        active = MotionIntent(0.1, 0.0, True)

        first = self.plan(planner, 0, active, MotionGate(False, False))
        self.assertEqual(first.packet.message_type, MSG_STOP)
        blocked = self.plan(planner, 1, active, MotionGate(False, False))
        self.assertEqual(blocked.packet.message_type, MSG_HEARTBEAT)
        self.assertEqual(blocked.reason, "motion_commands_disabled")
        still_blocked = self.plan(planner, 101, active, MotionGate(True, False))
        self.assertEqual(still_blocked.packet.message_type, MSG_HEARTBEAT)
        self.assertEqual(still_blocked.reason, "wheel_mapping_unconfirmed")

        old_session = planner.session_id
        timed_out = planner.plan(
            now_ms=102,
            intent=active,
            command_fresh=False,
            gate=MotionGate(False, False),
            track_width_m=0.10,
            channel_wheels=("lf", "lr", "rf", "rr"),
            channel_signs=(1, 1, 1, 1),
            wheel_target_limit_mmps=1000,
        )
        self.assertEqual(timed_out.packet.message_type, MSG_STOP)
        self.assertEqual(timed_out.reason, "inactive_stop")
        self.assertNotEqual(planner.session_id, old_session)

    def test_requires_device_readiness_session_and_center_before_arm(self):
        planner = self.make_planner()
        gate = MotionGate(True, True)
        centered = MotionIntent(0.0, 0.0, True)
        forward = MotionIntent(0.2, 0.0, True)

        first = self.plan(planner, 0, centered, gate)
        self.assertEqual(first.packet.message_type, MSG_STOP)
        waiting = self.plan(planner, 1, centered, gate)
        self.assertEqual(waiting.reason, "device_motion_not_ready")
        self.assertEqual(waiting.packet.message_type, MSG_HEARTBEAT)

        planner.observe(telemetry_packet(session_id=planner.session_id))
        ready = self.plan(planner, 2, centered, gate)
        self.assertEqual(ready.reason, "centered_ready")
        self.assertIsNone(ready.packet)

        arm = self.plan(planner, 3, forward, gate)
        self.assertEqual(arm.packet.message_type, MSG_ARM)
        planner.observe(
            response_packet(
                MSG_ARM,
                session_id=planner.session_id,
                sequence=arm.packet.sequence,
            )
        )
        awaiting_telemetry = self.plan(planner, 4, forward, gate)
        self.assertEqual(awaiting_telemetry.reason, "arm_pending")
        self.assertIsNone(awaiting_telemetry.packet)
        planner.observe(
            telemetry_packet(
                session_id=planner.session_id,
                sequence=2,
                state=STATE_ARMED,
            )
        )
        wheel = self.plan(planner, 5, forward, gate)
        self.assertEqual(wheel.packet.message_type, MSG_WHEEL_TARGET)
        self.assertEqual(
            (waiting.packet.sequence, arm.packet.sequence, wheel.packet.sequence),
            (1, 2, 3),
        )
        self.assertEqual(wheel.wheel_targets_mmps, (200, 200, 200, 200))
        self.assertEqual(
            struct.unpack("<4h", wheel.packet.payload),
            (200, 200, 200, 200),
        )

        old_session = planner.session_id
        stopped = planner.plan(
            now_ms=6,
            intent=MotionIntent(0.0, 0.0, False),
            command_fresh=True,
            gate=gate,
            track_width_m=0.10,
            channel_wheels=("lf", "lr", "rf", "rr"),
            channel_signs=(1, 1, 1, 1),
            wheel_target_limit_mmps=1000,
        )
        self.assertEqual(stopped.packet.message_type, MSG_STOP)
        self.assertNotEqual(planner.session_id, old_session)
        self.assertFalse(planner.session_ready)

    def test_centering_while_disabled_does_not_satisfy_enable_gate(self):
        planner = self.make_planner()
        centered = MotionIntent(0.0, 0.0, True)
        forward = MotionIntent(0.1, 0.0, True)

        self.plan(planner, 0, centered, MotionGate(False, False))
        heartbeat = self.plan(planner, 1, centered, MotionGate(False, False))
        planner.observe(
            response_packet(
                MSG_HEARTBEAT,
                session_id=planner.session_id,
                sequence=heartbeat.packet.sequence,
            )
        )
        planner.observe(telemetry_packet(session_id=planner.session_id))

        blocked = self.plan(planner, 2, forward, MotionGate(True, True))
        self.assertEqual(blocked.reason, "input_not_centered")
        self.assertIsNone(blocked.packet)

    def test_motion_locked_nack_blocks_repeated_arm_until_new_telemetry(self):
        planner = self.make_planner()
        gate = MotionGate(True, True)
        centered = MotionIntent(0.0, 0.0, True)
        forward = MotionIntent(0.1, 0.0, True)

        self.plan(planner, 0, centered, gate)
        heartbeat = self.plan(planner, 1, centered, gate)
        planner.observe(
            response_packet(
                MSG_HEARTBEAT,
                session_id=planner.session_id,
                sequence=heartbeat.packet.sequence,
            )
        )
        planner.observe(telemetry_packet(session_id=planner.session_id))
        self.plan(planner, 2, centered, gate)
        arm = self.plan(planner, 3, forward, gate)
        planner.observe(
            response_packet(
                MSG_ARM,
                session_id=planner.session_id,
                sequence=arm.packet.sequence,
                status=STATUS_MOTION_LOCKED,
                nack=True,
            )
        )

        blocked = self.plan(planner, 103, forward, gate)
        self.assertEqual(blocked.reason, "device_motion_not_ready")
        self.assertEqual(blocked.packet.message_type, MSG_HEARTBEAT)

    def test_device_session_loss_forces_stop_and_new_centered_session(self):
        planner = self.make_planner()
        gate = MotionGate(True, True)
        centered = MotionIntent(0.0, 0.0, True)

        self.plan(planner, 0, centered, gate)
        heartbeat = self.plan(planner, 1, centered, gate)
        planner.observe(
            response_packet(
                MSG_HEARTBEAT,
                session_id=planner.session_id,
                sequence=heartbeat.packet.sequence,
            )
        )
        self.assertTrue(planner.session_ready)
        old_session = planner.session_id

        planner.observe(telemetry_packet(session_id=0, sequence=2))
        self.assertNotEqual(planner.session_id, old_session)
        self.assertFalse(planner.session_ready)
        stopped = self.plan(planner, 2, centered, gate)
        self.assertEqual(stopped.packet.message_type, MSG_STOP)


if __name__ == "__main__":
    unittest.main()
