"""只读审查的独立协议夹具；不创建批准文件或导入运动控制台。"""
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from m2a_run_review import ReviewError, main, review_run


def wire(kind, payload=b'', session=0, sequence=0):
    data = bytes([1, kind]) + struct.pack('<HII', len(payload), session, sequence) + payload
    return b'\xa5\x5a' + data + struct.pack('<I', zlib.crc32(data))


class RunReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)

    def fixture(self, counts=(0, 65534, 1, 1), channel=1):
        self.rows = []
        self.clock = 0

        def event(direction, data):
            self.clock += .001
            self.rows.append(dict(direction=direction, hex=data.hex(), monotonic=self.clock))

        def send(kind, payload=b'', session=0, sequence=0):
            frame = wire(kind, payload, session, sequence)
            event('TX_ATTEMPT', frame)
            event('TX_COMPLETE', frame)
            state = 2 if kind in (2, 7) else 1
            event('RX', wire(0x81, bytes([kind, 0, state, 0]), session, sequence))

        send(4)
        first = last = None
        for i, count in enumerate(counts):
            if i == 1:
                send(1, session=77, sequence=1)
                send(2, session=77, sequence=2)
                send(7, struct.pack('<BbH', channel, 1, 50), session=77, sequence=3)
            if i == len(counts)-2:
                send(4)
            state = 2 if 0 < i < len(counts)-2 else 1
            values = [0]*4; values[channel] = count
            deltas = [0]*4
            if i:
                bits = 16 if channel in (1, 3) else 32
                half = 1 << (bits-1)
                deltas[channel] = (count-counts[i-1]+half) % (1 << bits)-half
            payload = bytes([state, 0, 1, 1]) + struct.pack('<4i4hHH4BI',
                *values, *deltas, 1325, 11745, 0, 2, 1, 2, 0)
            event('RX', wire(0x80, payload, 77 if state == 2 else 0, i+1))
            last = dict(encoder_count=values, sequence=i+1)
            first = first or last
        self.summary = dict(digital_run_pass=True, serial_closed=True,
                            initial_telemetry=first, final_telemetry=last)
        self.save()

    def save(self):
        (self.path/'result.json').write_text(json.dumps(self.summary))
        (self.path/'serial.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in self.rows))

    def mutate_rx(self, kind, mutate):
        for row in self.rows:
            data = bytes.fromhex(row['hex'])
            if row['direction'] == 'RX' and data[3] == kind:
                changed = bytearray(data[:-4]); mutate(changed)
                row['hex'] = (changed+struct.pack('<I', zlib.crc32(changed[2:]))).hex()
                return
        self.fail('fixture frame missing')

    def test_small_bidirectional_change_is_not_motion_pass(self):
        self.fixture(); r=review_run(self.path); m=r['channels']['MB']
        self.assertTrue(r['digital_audit_pass'])
        self.assertEqual((m['net'],m['path'],m['reversals']), (1,5,1))
        self.assertEqual(m['pattern'],'BIDIRECTIONAL_CHANGE')
        self.assertEqual(r['physical_startup'],'NOT_ASSESSED')

    def test_continuous_negative_change_is_still_not_physical_pass(self):
        self.fixture((65528,65523,65503,65479,65454,65429,65415,65415))
        r=review_run(self.path);m=r['channels']['MB']
        self.assertEqual((m['net'],m['longest_same_direction_intervals']),(-113,6))
        self.assertEqual(m['pattern'],'ONE_DIRECTION_CHANGE')
        self.assertEqual(r['physical_direction'],'NOT_ASSESSED')
        self.assertEqual(r['physical_stop'],'NOT_ASSESSED')

    def test_zero_counts(self):
        self.fixture((0,0,0,0))
        self.assertEqual(review_run(self.path)['channels']['MB']['pattern'],'NO_CHANGE')

    def test_signed_32_bit_wrap(self):
        self.fixture((2147483647,-2147483648,-2147483647,-2147483647),channel=0)
        self.assertEqual(review_run(self.path)['channels']['MA']['net'],2)

    def test_positive_16_bit_wrap(self):
        self.fixture((65535,0,1,1))
        self.assertEqual(review_run(self.path)['channels']['MB']['net'],2)

    def test_fragmented_receive(self):
        self.fixture(); split=[]
        for row in self.rows:
            if row['direction']=='RX':
                split.extend(dict(row,hex=f'{b:02x}') for b in bytes.fromhex(row['hex']))
            else: split.append(row)
        self.rows=split;self.save()
        self.assertTrue(review_run(self.path)['digital_audit_pass'])

    def test_bad_crc(self):
        self.fixture();self.rows[-1]['hex']=self.rows[-1]['hex'][:-2]+'ff';self.save()
        with self.assertRaisesRegex(ReviewError,'CRC'):review_run(self.path)

    def test_incomplete_receive(self):
        self.fixture();self.rows[-1]['hex']=self.rows[-1]['hex'][:-2];self.save()
        with self.assertRaisesRegex(ReviewError,'未完成帧'):review_run(self.path)

    def test_incomplete_send(self):
        self.fixture();self.rows=[r for i,r in enumerate(self.rows) if i!=1];self.save()
        with self.assertRaisesRegex(ReviewError,'尝试与完成'):review_run(self.path)

    def test_duplicate_ack(self):
        self.fixture();self.rows.insert(3,dict(self.rows[2]));self.save()
        with self.assertRaisesRegex(ReviewError,'数量不匹配'):review_run(self.path)

    def test_ack_identity(self):
        self.fixture();self.mutate_rx(0x81,lambda b:b.__setitem__(6,99));self.save()
        with self.assertRaisesRegex(ReviewError,'ACK身份'):review_run(self.path)

    def test_nack_prevents_digital_pass(self):
        self.fixture();self.mutate_rx(0x81,lambda b:b.__setitem__(3,0x82));self.save()
        self.assertFalse(review_run(self.path)['digital_audit_pass'])

    def test_summary_mismatch(self):
        self.fixture();self.summary['final_telemetry']['encoder_count']=[0,999,0,0];self.save()
        with self.assertRaisesRegex(ReviewError,'汇总'):review_run(self.path)

    def test_time_backwards_and_nan(self):
        for value in (-1,float('nan')):
            with self.subTest(value=value):
                self.fixture();self.rows[-1]['monotonic']=value;self.save()
                with self.assertRaises(ReviewError):review_run(self.path)

    def test_missing_sequence(self):
        self.fixture();self.mutate_rx(0x80,lambda b:b.__setitem__(10,0));self.save()
        with self.assertRaisesRegex(ReviewError,'序号不连续'):review_run(self.path)

    def test_count_delta_disagreement(self):
        self.fixture()
        row=self.rows[-1];b=bytearray.fromhex(row['hex']);b[36]=7
        row['hex']=(b[:-4]+struct.pack('<I',zlib.crc32(b[2:-4]))).hex();self.save()
        with self.assertRaisesRegex(ReviewError,'增量不一致'):review_run(self.path)

    def test_no_post_stop_telemetry(self):
        self.fixture();last_stop=max(i for i,r in enumerate(self.rows)
            if r['direction']=='TX_ATTEMPT' and bytes.fromhex(r['hex'])[3]==4)
        self.rows=[r for i,r in enumerate(self.rows) if i<last_stop or
                   not (r['direction']=='RX' and bytes.fromhex(r['hex'])[3]==0x80)]
        self.save()
        with self.assertRaisesRegex(ReviewError,'STOP确认后'):review_run(self.path)

    def test_reported_failure_and_parser_error(self):
        for key,value in [('digital_run_pass',False),('serial_closed',False),
                          ('parser_stats',{'crc_errors':1})]:
            with self.subTest(key=key):
                self.fixture();self.summary[key]=value;self.save()
                self.assertFalse(review_run(self.path)['digital_audit_pass'])

    def test_cli_is_read_only(self):
        self.fixture()
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.path.iterdir()}
        with redirect_stdout(io.StringIO()):self.assertEqual(main([str(self.path)]),0)
        after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.path.iterdir()}
        self.assertEqual(before,after)

    def test_missing_files_cli_returns_error(self):
        with redirect_stderr(io.StringIO()):self.assertEqual(main([str(self.path)]),2)

    def test_malformed_summary_cli_returns_error(self):
        for key in ('initial_telemetry','final_telemetry','parser_stats'):
            with self.subTest(key=key):
                self.fixture();self.summary[key]=None;self.save()
                with redirect_stderr(io.StringIO()):self.assertEqual(main([str(self.path)]),2)


if __name__=='__main__':
    unittest.main()
