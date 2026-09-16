import contextlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

from tests import test_m2a_calibration_console as legacy

console = legacy.console
profile = console.slowdrive


class SlowdriveConsoleTests(unittest.TestCase):
    def arguments(self, root):
        firmware = root/'fake.bin'
        firmware.write_bytes(profile.MANIFEST)
        args = legacy.M2AConsoleTests.arguments(self, firmware, console.sha256_file(firmware))
        args.channel='MB'; args.trigger_mode='one-shot'; args.one_shot_profile=profile.PROFILE
        args.approval_code=profile.APPROVAL_CODE; args.run_approval=str(root/'approval.json')
        (root/'approval.json').write_text(json.dumps(dict(
            approved=True,profile=profile.PROFILE,channel='MB',direction='plus',duty_permille=50,
            max_session_ms=600,firmware_sha256=args.expected_sha256,
            user_message='OFFLINE TEST FIXTURE ONLY; no device authorization')))
        return args

    def h6_arguments(self, root, channel='MA', direction='minus', duty=80):
        args = self.arguments(root)
        firmware = root/'fake.bin'
        firmware.write_bytes(profile.H6_MANIFEST)
        args.expected_sha256 = console.sha256_file(firmware)
        args.channel = channel
        args.direction = direction
        args.duty_permille = duty
        args.one_shot_profile = profile.H6_PROFILE
        args.approval_code = profile.H6_APPROVAL_CODE
        Path(args.run_approval).write_text(json.dumps(dict(
            approved=True, profile=profile.H6_PROFILE, channel=channel,
            direction=direction, duty_permille=duty, max_session_ms=600,
            firmware_sha256=args.expected_sha256,
            user_message='OFFLINE H6 TEST FIXTURE ONLY; no device authorization')))
        return args

    def h6_r2_arguments(self, root):
        args = self.arguments(root)
        firmware = root/'fake.bin'
        firmware.write_bytes(profile.H6_R2_MANIFEST)
        args.expected_sha256 = console.sha256_file(firmware)
        args.channel = 'MC'
        args.direction = 'plus'
        args.duty_permille = 80
        args.max_session_ms = profile.H6_R2_NONZERO_WINDOW_MS
        args.one_shot_profile = profile.H6_R2_PROFILE
        args.approval_code = profile.H6_R2_APPROVAL_CODE
        Path(args.run_approval).write_text(json.dumps(dict(
            approved=True, profile=profile.H6_R2_PROFILE, channel='MC',
            direction='plus', duty_permille=80,
            max_session_ms=profile.H6_R2_NONZERO_WINDOW_MS,
            firmware_sha256=args.expected_sha256,
            user_message='OFFLINE H6-R2 TEST FIXTURE ONLY; no device authorization')))
        return args

    def test_exact_inputs_and_artifact(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(console.sys.stdin,'isatty',return_value=True):
            args=self.arguments(Path(tmp))
            self.assertEqual(console.validate_execution_inputs(args),(1,1))
            cases=[('channel','MA'),('channel','MC'),('channel','MD'),('direction','minus'),
                   ('duty_permille',0),('duty_permille',49),('duty_permille',80),
                   ('duty_permille',120),('max_session_ms',601),('max_session_ms',0),
                   ('trigger_mode','hold-space'),('approval_code',console.ONE_SHOT_APPROVAL_CODE),
                   ('one_shot_profile','standard-50'),('expected_sha256','0'*64)]
            for key,value in cases:
                original=getattr(args,key); setattr(args,key,value)
                with self.subTest(key=key,value=value), self.assertRaises(console.CalibrationConsoleError):
                    console.validate_execution_inputs(args)
                setattr(args,key,original)
            Path(args.firmware_bin).write_bytes(b'old M2A artifact')
            with self.assertRaises(console.CalibrationConsoleError): console.validate_execution_inputs(args)

    def test_approval_consumed_even_if_cancelled_and_no_device_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=self.arguments(Path(tmp))
            with mock.patch.object(console.sys.stdin,'isatty',return_value=True), \
                    mock.patch.object(console,'_prepare_one_shot',side_effect=KeyboardInterrupt), \
                    mock.patch.object(console,'PosixSerialPort') as port, \
                    contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(KeyboardInterrupt): console.run_console(args)
                with self.assertRaises(FileExistsError): console.run_console(args)
                port.assert_not_called()
            self.assertTrue(Path(args.run_approval+'.consumed').is_file())

    def test_h6_exact_per_run_matrix_and_artifact_binding(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(console.sys.stdin, 'isatty', return_value=True):
            root = Path(tmp)
            for channel in console.CHANNELS:
                for direction in console.DIRECTIONS:
                    for duty in (50, 80, 120):
                        args = self.h6_arguments(root, channel, direction, duty)
                        self.assertEqual(console.validate_execution_inputs(args),
                                         (console.CHANNELS[channel],
                                          console.DIRECTIONS[direction]))
            args = self.h6_arguments(root)
            for key, value in [('duty_permille', 49), ('duty_permille', 121),
                               ('max_session_ms', 601),
                               ('approval_code', profile.APPROVAL_CODE),
                               ('one_shot_profile', profile.PROFILE)]:
                original = getattr(args, key)
                setattr(args, key, value)
                with self.subTest(key=key, value=value), \
                        self.assertRaises(console.CalibrationConsoleError):
                    console.validate_execution_inputs(args)
                setattr(args, key, original)
            Path(args.firmware_bin).write_bytes(profile.MANIFEST)
            args.expected_sha256 = console.sha256_file(Path(args.firmware_bin))
            with self.assertRaises(console.CalibrationConsoleError):
                console.validate_execution_inputs(args)

    def test_h6_r2_exact_mc_plus_80_envelope_binding(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(console.sys.stdin, 'isatty', return_value=True):
            root = Path(tmp)
            args = self.h6_r2_arguments(root)
            self.assertEqual(console.validate_execution_inputs(args), (2, 1))
            for key, value in [('channel', 'MA'), ('channel', 'MD'),
                               ('direction', 'minus'), ('duty_permille', 79),
                               ('duty_permille', 120), ('max_session_ms', 1799),
                               ('max_session_ms', 1801),
                               ('approval_code', profile.H6_APPROVAL_CODE),
                               ('one_shot_profile', profile.H6_PROFILE)]:
                original = getattr(args, key)
                setattr(args, key, value)
                with self.subTest(key=key, value=value), \
                        self.assertRaises(console.CalibrationConsoleError):
                    console.validate_execution_inputs(args)
                setattr(args, key, original)
            Path(args.firmware_bin).write_bytes(profile.H6_MANIFEST)
            args.expected_sha256 = console.sha256_file(Path(args.firmware_bin))
            with self.assertRaises(console.CalibrationConsoleError):
                console.validate_execution_inputs(args)

    def test_missing_or_changed_approval_does_not_consume(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=self.arguments(Path(tmp)); path=Path(args.run_approval)
            record=json.loads(path.read_text()); record['approved']=False
            path.write_text(json.dumps(record))
            with self.assertRaises(ValueError): profile.consume(args)
            self.assertFalse(Path(args.run_approval+'.consumed').exists())

    def run_fake(self, fault=None, version=1, legacy_profile=False, h6=False,
                 r2=False):
        with tempfile.TemporaryDirectory() as tmp:
            args=(self.h6_r2_arguments(Path(tmp)) if r2 else
                  (self.h6_arguments(Path(tmp), 'MD', 'minus', 120)
                   if h6 else self.arguments(Path(tmp))))
            if legacy_profile: args.one_shot_profile='standard-50'
            link=legacy.FakeLink(fault); link.other_channel=0
            original=legacy.telemetry
            def telemetry(*a,**kw):
                frame=original(*a,**kw); packet=console.PacketParser().feed(frame)[0]
                payload=bytearray(packet.payload); payload[34]=version
                return console.encode_packet(console.Packet(packet.message_type, packet.session_id,
                                                            packet.sequence,bytes(payload)))
            def key(timeout):
                link.now+=min(0.001,max(0.0,timeout))
                has_output=any(p.message_type==console.MSG_M2A_CALIBRATION_HOLD for _,p in link.writes)
                if has_output and fault=='cancel': return 'q'
                if has_output and fault=='eof': raise console.CalibrationConsoleError('terminal input closed')
                if has_output and fault=='stall' and not link.delay_injected:
                    link.delay_injected=True; link.now+=0.080
                return None
            result=error=None
            with mock.patch.object(legacy,'telemetry',side_effect=telemetry), \
                    mock.patch.object(console.time,'monotonic',side_effect=lambda:link.now), \
                    mock.patch.object(console,'_operator_key',side_effect=key), \
                    contextlib.redirect_stdout(io.StringIO()):
                try: result=console._run_console(args,link)
                except BaseException as exc: error=exc
            self.assertTrue(link.closed)
            self.assertEqual(link.writes[-1][1].message_type,console.MSG_STOP)
            arms=[p for _,p in link.writes if p.message_type==console.MSG_ARM]
            self.assertLessEqual(len(arms),1)
            outputs=[(t,p) for t,p in link.writes if p.message_type==console.MSG_M2A_CALIBRATION_HOLD]
            for t,p in outputs:
                expected = ((2, 1, 80) if r2 else
                            ((3, -1, 120) if h6 else (1, 1, 50)))
                self.assertEqual(struct.unpack('<BbH',p.payload), expected)
                if not r2:
                    self.assertLessEqual(t-link.armed_at,.600)
            return link,result,error,arms,outputs

    def test_single_arm_fixed_output_deadline_and_stop(self):
        link,result,error,arms,outputs=self.run_fake()
        self.assertIsNone(error); self.assertEqual(len(arms),1)
        self.assertGreater(len(outputs),0); self.assertLessEqual(len(outputs),24)
        self.assertTrue(result['stop_confirmed'])
        stop=next(t for t,p in link.writes if p.message_type==console.MSG_STOP and t>link.armed_at)
        self.assertLessEqual(stop-link.armed_at,.601)

    def test_h6_single_arm_selected_output_deadline_and_stop(self):
        link,result,error,arms,outputs=self.run_fake(version=11,h6=True)
        self.assertIsNone(error); self.assertEqual(len(arms),1)
        self.assertGreater(len(outputs),0); self.assertLessEqual(len(outputs),24)
        self.assertTrue(result['stop_confirmed'])
        self.assertEqual((result['channel'], result['direction'], result['duty_permille']),
                         ('MD', 'minus', 120))

    def test_h6_r2_deadline_is_anchored_to_first_nonzero_and_stops_once(self):
        link,result,error,arms,outputs=self.run_fake(version=12,r2=True)
        self.assertIsNone(error); self.assertEqual(len(arms),1)
        self.assertGreater(len(outputs),60)
        self.assertTrue(result['stop_confirmed'])
        first=outputs[0][0]
        stop=next(t for t,p in link.writes
                  if p.message_type==console.MSG_STOP and t>link.armed_at)
        self.assertLessEqual(stop-first,1.800001)
        self.assertLessEqual(stop-link.armed_at,2.500001)
        self.assertEqual(result['run_trace']['nonzero_deadline_monotonic'],
                         result['run_trace']['first_nonzero_tx_monotonic']+1.8)

    def test_h6_r2_faults_stop_close_and_never_rearm(self):
        for fault in ['missing_runtime_ack', 'nack', 'crc', 'fault', 'session',
                      'other_encoder', 'stall', 'cancel']:
            with self.subTest(fault=fault):
                _,_,error,arms,outputs=self.run_fake(fault,version=12,r2=True)
                if fault!='cancel': self.assertIsNotNone(error)
                self.assertLessEqual(len(arms),1)
                if fault=='missing_runtime_ack': self.assertEqual(len(outputs),1)

    def test_both_versions_reject_cross_profile_before_arm(self):
        for version,old in [(0,False),(1,True),(2,False)]:
            with self.subTest(version=version,old=old):
                _,_,error,arms,outputs=self.run_fake(version=version,legacy_profile=old)
                self.assertIsNotNone(error); self.assertEqual(arms,[]); self.assertEqual(outputs,[])

    def test_failures_stop_close_and_never_rearm(self):
        for fault in ['missing_runtime_ack','runtime_ack','wrong_runtime_command',
                      'nack','crc','fault','session','sequence','other_encoder','silent',
                      'missing_stop_ack','stop_write','eof','stall','cancel']:
            with self.subTest(fault=fault):
                _,_,error,_,outputs=self.run_fake(fault)
                if fault!='cancel': self.assertIsNotNone(error)
                if fault=='missing_runtime_ack': self.assertEqual(len(outputs),1)


if __name__=='__main__': unittest.main()
