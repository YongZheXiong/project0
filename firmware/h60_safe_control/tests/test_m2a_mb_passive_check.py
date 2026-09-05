"""MB 静止读取的伪串口检查；不打开硬件。"""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import m2a_mb_passive_check as check
from p0_base_bridge.h60_protocol import Packet, MSG_TELEMETRY, encode_packet


def frame(seq, mb=8, state=1):
    payload = struct.pack('<BBBB4i4hHHBBBBI', state, 0, 1, 1,
                          0, mb, 0, 0, 0, 0, 0, 0, 1338, 11861, 0, 2, 0, 2, 0)
    return encode_packet(Packet(MSG_TELEMETRY, 0, seq, payload))


class Port:
    def __init__(self, frames):
        self.frames = iter(frames)
        self.now = 0
        self.closed = False

    def read(self, maximum, timeout):
        self.now += 0.1
        return next(self.frames, b'')

    def close(self):
        self.closed = True

    def write(self, *args):
        raise AssertionError('被动检查禁止发送命令')


class PassiveTest(unittest.TestCase):
    def run_capture(self, frames):
        p = Port(frames)
        result, raw = check.capture(p, lambda: p.now)
        self.assertTrue(p.closed)
        self.assertEqual(result['tx'], [])
        self.assertLessEqual(p.now, 4.1)
        return result

    def test_static_nonzero_mb_baseline_is_allowed(self):
        r = self.run_capture(frame(i) for i in range(50))
        self.assertTrue(r['passive_check_pass'], r['errors'])

    def test_count_change_is_rejected(self):
        r = self.run_capture([frame(0), frame(1, mb=9)])
        self.assertIn('ENCODER_COUNT_CHANGED', str(r['errors']))

    def test_armed_state_is_rejected(self):
        r = self.run_capture([frame(0, state=2)])
        self.assertIn('UNSAFE_TELEMETRY', str(r['errors']))

    def test_bad_crc_is_rejected(self):
        data = bytearray(frame(0)); data[-1] ^= 1
        r = self.run_capture([bytes(data)])
        self.assertIn('crc_errors', str(r['errors']))

    def test_gap_and_missing_stream_are_rejected(self):
        for frames, error in [([frame(0), frame(2)], 'SEQUENCE_GAP'), ([], 'TELEMETRY_TIMEOUT')]:
            with self.subTest(error=error):
                r = self.run_capture(frames)
                self.assertIn(error, str(r['errors']))

    def test_read_error_closes_port(self):
        p = Port([])
        def broken(*args):
            raise OSError('disconnected')
        p.read = broken
        r, _ = check.capture(p, lambda: p.now)
        self.assertTrue(p.closed)
        self.assertFalse(r['passive_check_pass'])


if __name__ == '__main__':
    unittest.main()
