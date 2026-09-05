import importlib.util
from pathlib import Path
import unittest
from unittest import mock

from tests.test_m2a_calibration_console import FakeLink, console

path = Path(__file__).resolve().parents[1] / 'tools/m2a_uart_duplex_check.py'
spec = importlib.util.spec_from_file_location('duplex', path)
duplex = importlib.util.module_from_spec(spec)
spec.loader.exec_module(duplex)


class PairLink(FakeLink):
    def write(self, data, timeout_sec=0.05):
        packets = console.PacketParser().feed(data)
        for i, packet in enumerate(packets):
            super().write(console.encode_packet(packet), timeout_sec)
            if len(packets) == 2 and i == 1 and self.fault == 'drop_second':
                self.queue.pop()
        if self.fault == 'read_error' and packets[-1].message_type == console.MSG_HEARTBEAT:
            self.queue.clear()

    def read(self, maximum, timeout):
        if self.fault == 'read_error' and self.session:
            raise OSError('RX failed')
        data = super().read(maximum, timeout)
        if self.fault == 'corrupt' and self.session and data:
            data = data[:-1] + bytes([data[-1] ^ 1])
        return data


class DuplexTests(unittest.TestCase):
    def run_case(self, fault=None, counts=None):
        link = PairLink(fault=fault)
        if counts is not None:
            link.counts = counts
        with mock.patch.object(duplex.time, 'monotonic', side_effect=lambda: link.now), \
                mock.patch.object(duplex.protocol.time, 'monotonic', side_effect=lambda: link.now):
            result = duplex.capture(link)
        self.assertTrue(link.closed)
        self.assertLess(result['duration'], 4)
        self.assertTrue(all(p.message_type in (console.MSG_HEARTBEAT, console.MSG_STOP)
                            for _, p in link.writes))
        self.assertEqual(link.writes[-1][1].message_type, console.MSG_STOP)
        return result

    def test_all_pairs_confirmed_without_arm(self):
        result = self.run_case()
        self.assertTrue(result['communication_pass'], result['errors'])
        self.assertEqual(result['heartbeat_acks'], 120)
        self.assertEqual(result['final_telemetry']['state'], 1)
        self.assertEqual(result['final_telemetry']['session_id'], 0)

    def test_dropped_second_frame_stops_first_burst(self):
        result = self.run_case('drop_second')
        self.assertFalse(result['communication_pass'])
        self.assertEqual(result['bursts'], 0)
        self.assertEqual(result['heartbeat_acks'], 1)
        self.assertTrue(result['stop_confirmed'])

    def test_corrupt_or_failed_reads_stop(self):
        for fault in ('corrupt', 'read_error'):
            with self.subTest(fault=fault):
                self.assertFalse(self.run_case(fault)['communication_pass'])

    def test_nonzero_encoder_prevents_heartbeat(self):
        result = self.run_case(counts=[0, 1, 0, 0])
        self.assertFalse(result['communication_pass'])
        self.assertEqual(result['heartbeat_acks'], 0)


if __name__ == '__main__':
    unittest.main()
