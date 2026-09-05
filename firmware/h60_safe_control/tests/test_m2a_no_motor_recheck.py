"""无硬件测试：所有串口与时钟均为本地假对象。"""

import contextlib
import io
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import m2a_no_motor_recheck as recheck
from p0_base_bridge.h60_protocol import Packet, encode_packet, MSG_TELEMETRY, MSG_ACK


def telemetry(sequence, *, state=1, fault=0, version=(0, 2, 0),
              capability=2, count=0, self_test=1, session=0):
    payload = struct.pack('<BBBB4i4hHHBBBBI', state, fault, 1, self_test,
                          count, 0, 0, 0, 0, 0, 0, 0,
                          1338, 11861, *version, capability, 0)
    return encode_packet(Packet(MSG_TELEMETRY, session, sequence, payload))


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class FakePort:
    def __init__(self, events=None, *, ack=True, stop_error=False):
        self.clock = FakeClock()
        self.events = ([(0.05 + index * 0.1, telemetry(index + 1))
                        for index in range(50)] if events is None else list(events))
        self.ack = ack
        self.stop_error = stop_error
        self.writes = []
        self.closed = False

    def read(self, maximum, timeout):
        if self.events and self.events[0][0] <= self.clock.now + timeout:
            when, data = self.events.pop(0)
            self.clock.now = max(self.clock.now, when)
            if isinstance(data, BaseException):
                raise data
            assert len(data) <= maximum
            return data
        self.clock.now += max(timeout, 0.000001)
        return b''

    def write(self, data):
        # 任何潜在 ARM/心跳/校准输出都会直接使测试失败。
        if data != bytes.fromhex('a55a01040000000000000000000082f9a950'):
            raise AssertionError('只能发送固定 STOP')
        self.writes.append(data)
        if self.stop_error:
            raise OSError('simulated write failure')
        if self.ack:
            payload = bytes([4, 0, 1, 0])
            self.events.append((self.clock.now + 0.01,
                                encode_packet(Packet(MSG_ACK, 0, 0, payload))))
            self.events.sort(key=lambda item: item[0])

    def close(self):
        self.closed = True


class RecheckTest(unittest.TestCase):
    def run_capture(self, port):
        result, raw = recheck.capture(port, port.clock)
        self.assertTrue(port.closed)
        self.assertEqual(port.writes, [recheck.STOP_FRAME])
        self.assertLess(port.clock.now, 4.8)
        self.assertEqual(result['raw_bytes'], len(raw))
        return result, raw

    def test_good_stream_three_windows_and_exactly_one_stop(self):
        result, _ = self.run_capture(FakePort())
        self.assertTrue(result['communication_pass'], result['errors'])
        self.assertEqual(result['windows']['startup']['telemetry_count'], 10)
        self.assertEqual(result['windows']['formal']['telemetry_count'], 30)
        self.assertGreaterEqual(result['windows']['stop']['telemetry_count'], 3)
        self.assertTrue(result['stop_ack'])

    def test_truncated_startup_header_is_not_ignored(self):
        port = FakePort()
        prefix = b'old_tail' + bytes.fromhex('a55a01802800')
        port.events[0] = (0.05, prefix + telemetry(1))
        result, raw = self.run_capture(port)
        self.assertFalse(result['communication_pass'])
        self.assertIn('startup: crc_errors', result['errors'])
        self.assertNotIn('formal', result['windows'])
        self.assertTrue(raw.startswith(prefix))

    def test_leading_partial_tail_is_recorded_without_reset(self):
        port = FakePort()
        port.events[0] = (0.05, b'partial_tail' + telemetry(1))
        result, raw = self.run_capture(port)
        self.assertTrue(result['communication_pass'], result['errors'])
        self.assertEqual(result['parser_stats']['discarded_bytes'], 12)
        self.assertTrue(raw.startswith(b'partial_tail'))

    def test_formal_crc_error_stops(self):
        port = FakePort()
        corrupt = bytearray(telemetry(15)); corrupt[-1] ^= 1
        port.events[14] = (1.45, bytes(corrupt))
        result, _ = self.run_capture(port)
        self.assertIn('formal: crc_errors', result['errors'])
        self.assertFalse(result['communication_pass'])
        self.assertLess(result['windows']['formal']['duration'], 1.0)

    def test_formal_noise_is_not_ignored(self):
        port = FakePort()
        port.events[14] = (1.45, b'noise' + telemetry(15))
        result, _ = self.run_capture(port)
        self.assertIn('formal: discarded_bytes', result['errors'])

    def test_no_data_is_bounded_and_stop_attempted(self):
        result, _ = self.run_capture(FakePort(events=[], ack=False))
        self.assertIn('startup: TELEMETRY_TIMEOUT', result['errors'])
        self.assertIn('stop: ACK_MISSING', result['errors'])

    def test_unsafe_fields_always_fail(self):
        for changed in ({'state': 2}, {'fault': 1}, {'self_test': 0},
                        {'version': (0, 1, 1)}, {'capability': 0},
                        {'count': 1}, {'session': 9}):
            with self.subTest(changed=changed):
                port = FakePort()
                port.events[0] = (0.05, telemetry(1, **changed))
                result, _ = self.run_capture(port)
                self.assertIn('startup: UNSAFE_TELEMETRY', result['errors'])
                self.assertFalse(result['communication_pass'])

    def test_sequence_jump_is_not_hidden_at_phase_boundary(self):
        port = FakePort()
        port.events[10] = (1.05, telemetry(12))
        result, _ = self.run_capture(port)
        self.assertIn('formal: SEQUENCE_GAP', result['errors'])

    def test_sequence_wrap_is_accepted(self):
        port = FakePort(events=[(0.05 + i * 0.1, telemetry((2**32 - 5 + i) % 2**32))
                                for i in range(50)])
        result, _ = self.run_capture(port)
        self.assertTrue(result['communication_pass'], result['errors'])

    def test_read_exception_and_interrupt_close_with_stop(self):
        for error in (OSError('simulated read failure'), KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__):
                port = FakePort()
                port.events.insert(0, (0.001, error))
                result, _ = self.run_capture(port)
                self.assertFalse(result['communication_pass'])
                self.assertTrue(any(item.startswith('capture:') for item in result['errors']))

    def test_stop_write_failure_does_not_retry(self):
        result, _ = self.run_capture(FakePort(stop_error=True))
        self.assertFalse(result['communication_pass'])
        self.assertFalse(result['tx'][0]['write_completed'])

    def test_stop_ack_is_required(self):
        result, _ = self.run_capture(FakePort(ack=False))
        self.assertFalse(result['communication_pass'])
        self.assertIn('stop: ACK_MISSING', result['errors'])

    def test_version_and_length_errors_stop_during_startup(self):
        wrong_version = bytearray(telemetry(1)); wrong_version[2] = 2
        too_long = bytes.fromhex('a55a0180ffff') + b'\0' * 60
        for data, expected in ((bytes(wrong_version), 'version_errors'),
                               (too_long, 'length_errors')):
            with self.subTest(expected=expected):
                port = FakePort(); port.events[0] = (0.05, data)
                result, _ = self.run_capture(port)
                self.assertIn(f'startup: {expected}', result['errors'])
                self.assertNotIn('formal', result['windows'])

    def test_delayed_complete_frame_does_not_erase_timeout(self):
        events = [(0.01, telemetry(1)), (0.27, telemetry(2))]
        events += [(0.37 + i * 0.1, telemetry(3 + i)) for i in range(8)]
        result, _ = self.run_capture(FakePort(events=events))
        self.assertIn('startup: TELEMETRY_TIMEOUT', result['errors'])
        self.assertFalse(result['communication_pass'])

    def test_unexpected_ack_in_passive_window_fails(self):
        port = FakePort()
        port.events.insert(0, (0.01, encode_packet(Packet(MSG_ACK, 0, 0, bytes([4, 0, 1, 0])))))
        result, _ = self.run_capture(port)
        self.assertIn('startup: UNEXPECTED_PACKET_129', result['errors'])
        self.assertFalse(result['communication_pass'])

    def test_usb_identity_guard_rejects_debug_extra_or_wrong_path(self):
        com = SimpleNamespace(device='/dev/test-com', vid=0x1A86, pid=0x55D4)
        debug = SimpleNamespace(device='/dev/test-debug', vid=0x1A86, pid=0x7523)
        recheck.validate_usb_identity(com.device, [com])
        for devices, target in (([], com.device), ([debug], debug.device),
                                ([com, debug], com.device), ([com], '/dev/wrong')):
            with self.subTest(devices=devices, target=target):
                with self.assertRaises(ValueError):
                    recheck.validate_usb_identity(target, devices)

    def test_cli_requires_confirmation_before_open(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(recheck, 'PosixSerialPort') as opener:
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as caught:
                        recheck.main(['--port', '/dev/test', '--evidence-root', directory])
                self.assertEqual(caught.exception.code, 2)
                opener.assert_not_called()


if __name__ == '__main__':
    unittest.main()
