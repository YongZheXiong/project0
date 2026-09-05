import argparse
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock


TOOL = Path(__file__).resolve().parents[1] / "tools" / "m2a_calibration_console.py"
SPEC = importlib.util.spec_from_file_location("m2a_console", TOOL)
assert SPEC is not None and SPEC.loader is not None
console = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(console)


class M2AConsoleTests(unittest.TestCase):
    def arguments(self, firmware: Path, digest: str):
        return argparse.Namespace(
            evidence_root=str(firmware.parent),
            port="/fake/usb-com",
            approval_code=console.APPROVAL_CODE,
            firmware_bin=str(firmware),
            expected_sha256=digest,
            max_session_ms=600,
            duty_permille=50,
            channel="MA",
            direction="plus",
        )

    def test_hash_and_execution_inputs_must_match(self):
        with tempfile.TemporaryDirectory() as directory:
            firmware = Path(directory) / "m2a.bin"
            firmware.write_bytes(b"reviewed-m2a-artifact")
            digest = hashlib.sha256(firmware.read_bytes()).hexdigest()
            args = self.arguments(firmware, digest)
            with mock.patch.object(console.sys.stdin, "isatty", return_value=True):
                self.assertEqual(console.validate_execution_inputs(args), (0, 1))

            args.expected_sha256 = "0" * 64
            with mock.patch.object(console.sys.stdin, "isatty", return_value=True):
                with self.assertRaises(console.CalibrationConsoleError):
                    console.validate_execution_inputs(args)

            args.expected_sha256 = digest
            args.max_session_ms = 600
            args.duty_permille = 121
            with mock.patch.object(console.sys.stdin, "isatty", return_value=True):
                with self.assertRaises(console.CalibrationConsoleError):
                    console.validate_execution_inputs(args)

    def test_requires_approval_and_bounded_session(self):
        with tempfile.TemporaryDirectory() as directory:
            firmware = Path(directory) / "m2a.bin"
            firmware.write_bytes(b"x")
            digest = hashlib.sha256(b"x").hexdigest()
            args = self.arguments(firmware, digest)
            args.approval_code = "wrong"
            with mock.patch.object(console.sys.stdin, "isatty", return_value=True):
                with self.assertRaises(console.CalibrationConsoleError):
                    console.validate_execution_inputs(args)

            args.approval_code = console.APPROVAL_CODE
            args.max_session_ms = console.MAX_HOST_SESSION_MS + 1
            with mock.patch.object(console.sys.stdin, "isatty", return_value=True):
                with self.assertRaises(console.CalibrationConsoleError):
                    console.validate_execution_inputs(args)





# 所有运行回归均使用内存串口、伪时钟和伪键盘，不访问设备。
import contextlib
import io
import json
import struct
import os
import pty
import select
import subprocess
import sys
import threading
import time


def telemetry(sequence, state=1, session=0, counts=(0, 0, 0, 0), fault=0):
    payload = struct.pack('<BBBB4i4hHHBBBBI', state, fault, 1, 1,
                          *counts, 0, 0, 0, 0, 1338, 11861, 0, 2, 0, 2, 0)
    return console.encode_packet(console.Packet(console.MSG_TELEMETRY, session, sequence, payload))


class FakeLink:
    def __init__(self, fault=None):
        self.now = 0.0
        self.next_telemetry = 0.02
        self.telemetry_sequence = 0
        self.state = 1
        self.session = 0
        self.counts = [0, 0, 0, 0]
        self.queue = []
        self.writes = []
        self.closed = False
        self.armed_at = None
        self.ever_armed = False
        self.fault = fault
        self.injected = False
        self.delay_injected = False

    def write(self, data, timeout_sec=0.05):
        packet = console.PacketParser().feed(data)[0]
        self.writes.append((self.now, packet))
        if packet.message_type == console.MSG_STOP:
            self.state, self.session = 1, 0
            if self.ever_armed and self.fault == 'stop_write':
                raise OSError('STOP write failure')
        elif packet.message_type == console.MSG_HEARTBEAT:
            self.session = packet.session_id
        elif packet.message_type == console.MSG_ARM:
            self.state, self.session = 2, packet.session_id
            self.armed_at, self.ever_armed = self.now, True
        elif packet.message_type == console.MSG_M2A_CALIBRATION_HOLD:
            ch, direction, duty = struct.unpack('<BbH', packet.payload)
            if duty:
                self.counts[ch] += direction
        if self.ever_armed and packet.message_type == console.MSG_STOP and self.fault == 'missing_stop_ack':
            return
        response_sequence = packet.sequence
        if packet.message_type == console.MSG_HEARTBEAT and not self.ever_armed and self.fault == 'wrong_ack':
            response_sequence += 1
        if packet.message_type == console.MSG_M2A_CALIBRATION_HOLD and self.fault == 'runtime_ack':
            response_sequence += 100
        if packet.message_type == console.MSG_M2A_CALIBRATION_HOLD and self.fault == 'missing_runtime_ack':
            return
        response_type = console.MSG_ACK
        status = 0
        if packet.message_type == console.MSG_ARM and self.fault == 'nack':
            response_type, status = console.MSG_NACK, 1
        self.queue.append(console.encode_packet(console.Packet(response_type, packet.session_id,
                         response_sequence, bytes([
                             console.MSG_HEARTBEAT if (
                                 packet.message_type == console.MSG_M2A_CALIBRATION_HOLD
                                 and self.fault == 'wrong_runtime_command') else packet.message_type,
                             status, self.state, 0]))))

    def read(self, maximum, timeout):
        self.now += timeout
        chunks = self.queue[:]
        self.queue.clear()
        if self.now >= self.next_telemetry:
            self.next_telemetry = self.now + 0.05
            self.telemetry_sequence += 1
            seq, state, session = self.telemetry_sequence, self.state, self.session
            counts = list(self.counts)
            fault_code = 0
            if self.ever_armed and self.state == 2 and not self.injected:
                self.injected = True
                if self.fault == 'sequence': seq += 5
                if self.fault == 'fault': fault_code = 1
                if self.fault == 'session': session += 1
                if self.fault == 'other_encoder': counts[getattr(self, 'other_channel', 1)] += 1
            data = telemetry(seq, state, session, tuple(counts), fault_code)
            if self.ever_armed and self.state == 2 and self.fault == 'crc':
                data = data[:-1] + bytes([data[-1] ^ 1])
            if not (self.ever_armed and self.state == 2 and self.fault == 'silent'):
                chunks.append(data)
        result = b''.join(chunks)
        assert len(result) <= maximum
        return result

    def close(self):
        self.closed = True


class RuntimeTests(unittest.TestCase):
    arguments = M2AConsoleTests.arguments

    def run_fake(self, *, fault=None, key=' ', outer=False, mode='hold-space', profile='standard-50'):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        firmware = Path(temp.name) / 'm2a.bin'
        firmware.write_bytes(b'reviewed-m2a-artifact')
        args = self.arguments(firmware, console.sha256_file(firmware))
        args.trigger_mode = mode
        if mode == 'one-shot':
            args.approval_code = console.ONE_SHOT_APPROVAL_CODE
        args.one_shot_profile = profile
        if profile == console.MB80_PROFILE:
            args.channel, args.direction, args.duty_permille = 'MB', 'plus', 80
            args.approval_code = console.MB80_APPROVAL_CODE
        link = FakeLink(fault)
        link.other_channel = 0 if args.channel != 'MA' else 1
        stdin = mock.Mock()
        stdin.fileno.return_value = 42
        stdin.isatty.return_value = True
        def select_fake(*unused):
            link.now += 0.005
            if fault == 'interrupt': raise KeyboardInterrupt()
            has_output = any(p.message_type == console.MSG_M2A_CALIBRATION_HOLD
                             and struct.unpack('<BbH', p.payload)[2] for _, p in link.writes)
            if fault == 'stall' and has_output and not link.delay_injected:
                link.delay_injected = True
                link.now += .080
            if fault in ('cancel_after_output', 'eof_after_output') and has_output:
                return ([stdin], [], [])
            return ([stdin] if key is not None else [], [], [])
        def read_fake(fd, size):
            if fault == 'cancel_after_output': return b'q'
            if fault == 'eof_after_output': return b''
            return (key or '').encode()
        error = None
        result = None
        with contextlib.ExitStack() as stack:
            for target, value in (
                (console.time, {'monotonic': lambda: link.now}),
                (console.select, {'select': select_fake}),
                (console.os, {'read': read_fake}),
                (console.sys, {'stdin': stdin}),
                (console.termios, {'tcgetattr': lambda fd: [], 'tcsetattr': lambda *x: None}),
                (console.tty, {'setcbreak': lambda fd: None}),
                (console.secrets, {'randbits': lambda n: 77}),
            ):
                stack.enter_context(mock.patch.multiple(target, **value))
            stack.enter_context(mock.patch.object(console, 'PosixSerialPort', return_value=link))
            if outer and mode == 'one-shot':
                stack.enter_context(mock.patch.object(console, '_prepare_one_shot'))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            try:
                result = console.run_console(args) if outer else console._run_console(args, link)
            except BaseException as exc:
                error = exc
        self.assertTrue(link.closed)
        self.assertLess(link.now, 3.0)
        self.assertEqual(link.writes[-1][1].message_type, console.MSG_STOP)
        return link, result, error, Path(temp.name)

    def test_complete_run_and_post_stop_counts(self):
        link, result, error, _ = self.run_fake()
        self.assertIsNone(error)
        self.assertTrue(result['stop_confirmed'])
        self.assertEqual(result['final_telemetry']['state'], console.STATE_DISARMED)
        self.assertGreater(result['final_telemetry']['encoder_count'][0], 0)
        for when, packet in link.writes:
            if packet.message_type == console.MSG_M2A_CALIBRATION_HOLD:
                self.assertLessEqual(when - link.armed_at, 0.600)
                self.assertLessEqual(struct.unpack('<BbH', packet.payload)[2], 50)

    def test_missing_hold_ack_stops_before_another_output(self):
        link, _, error, _ = self.run_fake(mode='one-shot', key=None, fault='missing_runtime_ack')
        self.assertIn('missing runtime ACK', str(error))
        holds = [(t, p) for t, p in link.writes if p.message_type == console.MSG_M2A_CALIBRATION_HOLD]
        self.assertEqual(len(holds), 1)
        stop_at = next(t for t, p in link.writes
                       if t > holds[0][0] and p.message_type == console.MSG_STOP)
        self.assertLessEqual(stop_at - holds[0][0], .030)

    def test_ack_for_wrong_command_cannot_confirm_output(self):
        link, _, error, _ = self.run_fake(mode='one-shot', key=None, fault='wrong_runtime_command')
        self.assertIn('unexpected runtime ACK', str(error))
        self.assertEqual(sum(p.message_type == console.MSG_M2A_CALIBRATION_HOLD
                             for _, p in link.writes), 1)

    def test_no_key_never_requests_nonzero(self):
        link, _, error, _ = self.run_fake(key=None)
        self.assertIsNone(error)
        holds = [p for _, p in link.writes if p.message_type == console.MSG_M2A_CALIBRATION_HOLD]
        self.assertTrue(holds)
        self.assertTrue(all(struct.unpack('<BbH', p.payload)[2] == 0 for p in holds))

    def test_runtime_failures_always_close_and_stop(self):
        for fault in ('crc', 'sequence', 'fault', 'session', 'other_encoder', 'silent',
                      'nack', 'wrong_ack', 'missing_stop_ack', 'stop_write', 'interrupt'):
            with self.subTest(fault=fault):
                _, _, error, _ = self.run_fake(fault=fault)
                self.assertIsNotNone(error)

    def test_eof_stops(self):
        _, _, error, _ = self.run_fake(key='')
        self.assertIsInstance(error, console.CalibrationConsoleError)

    def test_original_stream_and_result_saved_on_pass_and_fail(self):
        for fault in (None, 'crc'):
            with self.subTest(fault=fault):
                _, _, error, directory = self.run_fake(fault=fault, outer=True)
                outputs = list(directory.glob('m2a_run_*'))
                self.assertEqual(len(outputs), 1)
                result = json.loads((outputs[0] / 'result.json').read_text())
                events = [json.loads(line) for line in (outputs[0] / 'serial.jsonl').read_text().splitlines()]
                self.assertEqual(result['digital_run_pass'], fault is None)
                self.assertTrue(result['serial_closed'])
                self.assertTrue(any(e['direction'] == 'RX' for e in events))
                self.assertTrue(any(e['direction'] == 'TX_COMPLETE' for e in events))
                self.assertEqual(error is None, fault is None)

    def test_log_failure_still_attempts_stop(self):
        link = FakeLink()
        stream = mock.Mock()
        stream.write.side_effect = OSError('disk full')
        wrapped = console.EvidencePort(link, stream)
        with self.assertRaises(OSError):
            wrapped.write(console.encode_packet(console.Packet(console.MSG_ARM, 1, 1)))
        self.assertEqual(link.writes, [])
        console._send_stop(wrapped)
        self.assertTrue(link.writes)
        self.assertTrue(all(p.message_type == console.MSG_STOP for _, p in link.writes))

    def test_key_lease_expiry_stops_without_rearm(self):
        original = console.LOCAL_KEY_LEASE_SEC
        # 单个空格后不再输入；超出本地租约后必须结束会话。
        link = FakeLink()
        args = argparse.Namespace(channel='MA', direction='plus', duty_permille=50, max_session_ms=600)
        stdin = mock.Mock()
        stdin.fileno.return_value = 42
        calls = 0
        def keys(*unused):
            nonlocal calls
            link.now += .005
            calls += 1
            return ([stdin] if calls == 1 else [], [], [])
        with mock.patch.object(console.time, 'monotonic', side_effect=lambda: link.now), \
                mock.patch.object(console.select, 'select', side_effect=keys), \
                mock.patch.object(console.os, 'read', return_value=b' '), \
                mock.patch.object(console.sys, 'stdin', stdin), \
                mock.patch.object(console.termios, 'tcgetattr', return_value=[]), \
                mock.patch.object(console.termios, 'tcsetattr'), \
                mock.patch.object(console.tty, 'setcbreak'), \
                contextlib.redirect_stdout(io.StringIO()):
            console._run_console(args, link)
        active = [(t, p) for t, p in link.writes if p.message_type == console.MSG_M2A_CALIBRATION_HOLD
                  and struct.unpack('<BbH', p.payload)[2]]
        stops = [t for t, p in link.writes if p.message_type == console.MSG_STOP and t > link.armed_at]
        self.assertTrue(active)
        self.assertLessEqual(stops[0] - active[0][0], original + .010)
        self.assertEqual(sum(p.message_type == console.MSG_ARM for _, p in link.writes), 1)

    def test_bad_frame_after_matching_ack_not_hidden(self):
        link = FakeLink()
        link.write(console.encode_packet(console.Packet(console.MSG_STOP)))
        damaged = bytearray(telemetry(1)); damaged[-1] ^= 1
        link.queue.append(bytes(damaged))
        with mock.patch.object(console.time, 'monotonic', side_effect=lambda: link.now):
            with self.assertRaises(console.CalibrationConsoleError):
                console._wait_packet(link, console.CheckedParser(), lambda p: p.message_type == console.MSG_ACK, .2)


class OneShotTests(unittest.TestCase):
    arguments = M2AConsoleTests.arguments
    run_fake = RuntimeTests.run_fake
    def test_one_shot_needs_separate_code_and_tighter_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            firmware = Path(directory) / 'm2a.bin'
            firmware.write_bytes(b'x')
            args = self.arguments(firmware, console.sha256_file(firmware))
            args.trigger_mode = 'one-shot'
            with mock.patch.object(console.sys.stdin, 'isatty', return_value=True):
                with self.assertRaises(console.CalibrationConsoleError):
                    console.validate_execution_inputs(args)
                args.approval_code = console.ONE_SHOT_APPROVAL_CODE
                console.validate_execution_inputs(args)
                for field, value in [('duty_permille', 51), ('max_session_ms', 601)]:
                    original = getattr(args, field)
                    setattr(args, field, value)
                    with self.assertRaises(console.CalibrationConsoleError):
                        console.validate_execution_inputs(args)
                    setattr(args, field, original)

    def test_one_shot_runs_without_space_once_and_reports_duration(self):
        link, result, error, _ = self.run_fake(mode='one-shot', key=None)
        self.assertIsNone(error)
        holds = [(t, p) for t, p in link.writes
                 if p.message_type == console.MSG_M2A_CALIBRATION_HOLD]
        self.assertGreater(len(holds), 10)
        self.assertTrue(all(struct.unpack('<BbH', p.payload) == (0, 1, 50) for _, p in holds))
        self.assertEqual(sum(p.message_type == console.MSG_ARM for _, p in link.writes), 1)
        self.assertTrue(all(t - link.armed_at <= .600 for t, _ in holds))
        stop_time = next(t for t, p in link.writes if t > link.armed_at and p.message_type == console.MSG_STOP)
        self.assertLessEqual(stop_time - link.armed_at, .606)
        trace = result['run_trace']
        self.assertEqual(trace['exit_reason'], 'session_limit')
        self.assertGreater(trace['nonzero_tx_to_stop_attempt_ms'], 400)
        self.assertEqual(trace['nonzero_commands'], len(holds))
        self.assertTrue(result['stop_confirmed'])

    def test_one_shot_faults_eof_and_stall_do_not_rearm(self):
        for fault in ('crc', 'sequence', 'fault', 'session', 'other_encoder', 'silent',
                      'nack', 'wrong_ack', 'runtime_ack', 'missing_stop_ack', 'stop_write',
                      'interrupt', 'eof_after_output', 'stall'):
            with self.subTest(fault=fault):
                link, _, error, _ = self.run_fake(mode='one-shot', key=None, fault=fault)
                self.assertIsNotNone(error)
                self.assertLessEqual(sum(p.message_type == console.MSG_ARM for _, p in link.writes), 1)
                if fault == 'stall':
                    self.assertIn('refusing to resume', str(error))
                    self.assertEqual(sum(p.message_type == console.MSG_M2A_CALIBRATION_HOLD
                                         for _, p in link.writes), 1)

    def test_one_shot_operator_key_stops_after_output(self):
        link, result, error, _ = self.run_fake(mode='one-shot', key=None, fault='cancel_after_output')
        self.assertIsNone(error)
        self.assertEqual(result['run_trace']['exit_reason'], 'operator_key')
        self.assertTrue(result['stop_confirmed'])
        self.assertLess(result['run_trace']['nonzero_tx_to_stop_attempt_ms'], 20)

    def test_one_shot_failure_keeps_trace_and_raw_evidence(self):
        _, _, error, directory = self.run_fake(mode='one-shot', key=None, fault='stall', outer=True)
        self.assertIsNotNone(error)
        result = json.loads(next(directory.glob('m2a_run_*/result.json')).read_text())
        self.assertFalse(result['digital_run_pass'])
        self.assertTrue(result['serial_closed'])
        self.assertIn('refusing to resume', result['run_trace']['exit_reason'])
        self.assertEqual(result['run_trace']['nonzero_commands'], 1)


class OperatorGateTests(unittest.TestCase):
    def gate(self, events):
        now = [0.0]
        trace = {}
        keys = iter(events)
        def read_key(timeout):
            event = next(keys, None)
            now[0] += timeout if event is None else min(timeout, .01)
            if isinstance(event, BaseException): raise event
            return event
        stdin = mock.Mock()
        stdin.fileno.return_value = 42
        args = argparse.Namespace(channel='MB', direction='plus', duty_permille=50, max_session_ms=600)
        with mock.patch.object(console, '_operator_key', side_effect=read_key), \
                mock.patch.object(console.time, 'monotonic', side_effect=lambda: now[0]), \
                mock.patch.object(console.sys, 'stdin', stdin), \
                mock.patch.object(console.termios, 'tcgetattr', return_value=['original']), \
                mock.patch.object(console.termios, 'tcsetattr') as restore, \
                mock.patch.object(console.tty, 'setcbreak'), \
                contextlib.redirect_stdout(io.StringIO()):
            error = None
            try:
                console._prepare_one_shot(args, trace)
            except BaseException as exc:
                error = exc
            restore.assert_called_once()
        return trace, error

    def test_enter_is_followed_by_full_countdown(self):
        trace, error = self.gate(['\n'])
        self.assertIsNone(error)
        self.assertGreaterEqual(trace['countdown_finished_monotonic'] - trace['operator_enter_monotonic'], 3)

    def test_timeout_cancel_double_enter_eof_or_interrupt_never_finish_countdown(self):
        for events in ([None], ['q'], ['\n', 'q'], ['\n', '\n'],
                       ['\n', console.CalibrationConsoleError('terminal input closed')], ['\n', KeyboardInterrupt()]):
            with self.subTest(events=events):
                trace, error = self.gate(events)
                self.assertIsNotNone(error)
                self.assertNotIn('countdown_finished_monotonic', trace)

    def test_outer_operator_cancellation_does_not_open_serial(self):
        with tempfile.TemporaryDirectory() as directory:
            firmware = Path(directory) / 'm2a.bin'; firmware.write_bytes(b'x')
            args = M2AConsoleTests.arguments(self, firmware, console.sha256_file(firmware))
            args.trigger_mode = 'one-shot'; args.approval_code = console.ONE_SHOT_APPROVAL_CODE
            with mock.patch.object(console.sys.stdin, 'isatty', return_value=True), \
                    mock.patch.object(console, '_prepare_one_shot', side_effect=KeyboardInterrupt()), \
                    mock.patch.object(console, 'PosixSerialPort') as serial, \
                    contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(KeyboardInterrupt): console.run_console(args)
                serial.assert_not_called()
            record = json.loads(next(Path(directory).glob('m2a_run_*/result.json')).read_text())
            self.assertFalse(record['serial_opened'])
            self.assertFalse(record['digital_run_pass'])


class DelayedAckLink(FakeLink):
    """按伪时钟延迟返回真实编码ACK，覆盖截止附近的发送/接收错位。"""
    def __init__(self, ack_delay=.00499, tail_fault=None):
        super().__init__()
        self.ack_delay = ack_delay
        self.tail_fault = tail_fault
        self.scheduled = []

    def write(self, data, timeout_sec=.05):
        packet = console.PacketParser().feed(data)[0]
        super().write(data, timeout_sec)
        if self.ever_armed and packet.message_type in (
                console.MSG_HEARTBEAT, console.MSG_M2A_CALIBRATION_HOLD):
            ack = self.queue.pop()
            tail = self.now - self.armed_at >= .54
            if tail and self.tail_fault == 'missing':
                return
            delay = .021 if tail and self.tail_fault == 'late' else self.ack_delay
            self.scheduled.append((self.now + delay, ack))

    def read(self, maximum, timeout):
        self.now += timeout
        self.queue.extend(data for due, data in self.scheduled if due <= self.now)
        self.scheduled = [(due, data) for due, data in self.scheduled if due > self.now]
        return super().read(maximum, 0.0)


class DeadlineAckTests(unittest.TestCase):
    def run_delayed(self, *, step=.00307, tail_fault=None, cancel=False, stall=False):
        link = DelayedAckLink(tail_fault=tail_fault)
        args = argparse.Namespace(channel='MA', direction='plus', duty_permille=50,
                                  max_session_ms=600, trigger_mode='one-shot')
        trace = {}
        injected = False

        def key(timeout):
            nonlocal injected
            link.now += min(step, timeout)
            if link.armed_at is not None and link.now - link.armed_at >= .54:
                if cancel:
                    return 'q'
                if stall and not injected:
                    injected = True
                    link.now += .080
            return None

        result = error = None
        with mock.patch.object(console.time, 'monotonic', side_effect=lambda: link.now), \
                mock.patch.object(console, '_operator_key', side_effect=key), \
                contextlib.redirect_stdout(io.StringIO()):
            try:
                result = console._run_console(args, link, trace)
            except BaseException as exc:
                error = exc
        self.assertTrue(link.closed)
        self.assertTrue(trace['stop_confirmed'])
        self.assertEqual(sum(p.message_type == console.MSG_ARM for _, p in link.writes), 1)
        return link, result, error, trace

    def test_normal_ack_near_session_end_is_not_false_failure(self):
        # 3.07ms轮询使旧实现于595.67ms发末命令，在4.99ms应答到达前结束。
        link, result, error, trace = self.run_delayed()
        self.assertIsNone(error)
        self.assertTrue(result['stop_confirmed'])
        self.assertLessEqual(trace['stop_attempt_monotonic'] - link.armed_at, .600001)

    def test_no_new_runtime_command_in_final_ack_budget(self):
        for step in (.0043, .0049, .005):
            with self.subTest(step=step):
                link, _, error, trace = self.run_delayed(step=step)
                self.assertIsNone(error)
                sends = [t for t, p in link.writes if t > link.armed_at
                         and p.message_type in (console.MSG_HEARTBEAT,
                                                console.MSG_M2A_CALIBRATION_HOLD)]
                self.assertTrue(sends)
                self.assertTrue(all(t < link.armed_at + .600 - .020 for t in sends))
                self.assertLessEqual(trace['stop_attempt_monotonic'] - link.armed_at, .600001)

    def test_exact_remaining_ack_budget_boundary(self):
        deadline = 10.0
        for remaining_ms, allowed in ((19, False), (20, False), (21, True)):
            with self.subTest(remaining_ms=remaining_ms), \
                    mock.patch.object(console.time, 'monotonic',
                                      return_value=deadline - remaining_ms / 1000):
                self.assertEqual(console._runtime_send_window_open(deadline), allowed)

    def test_missing_or_late_tail_ack_remains_failure(self):
        for fault in ('missing', 'late'):
            with self.subTest(fault=fault):
                link, result, error, trace = self.run_delayed(tail_fault=fault)
                self.assertIsNone(result)
                self.assertIn('runtime ACK', str(error))
                self.assertLessEqual(trace['stop_attempt_monotonic'] - link.armed_at, .600001)

    def test_late_operator_cancel_stops_without_waiting_for_ack(self):
        link, _, _, trace = self.run_delayed(cancel=True)
        self.assertLess(trace['stop_attempt_monotonic'] - link.armed_at, .550)
        self.assertEqual(link.writes[-1][1].message_type, console.MSG_STOP)

    def test_tail_scheduling_stall_never_resumes_output(self):
        link, _, error, trace = self.run_delayed(stall=True)
        self.assertIn('refusing to resume', str(error))
        runtime = [t for t, p in link.writes if p.message_type == console.MSG_M2A_CALIBRATION_HOLD]
        self.assertLess(max(runtime) - link.armed_at, .54)
        self.assertEqual(trace['phase'], 'stopped')


class PtyIntegrationTests(unittest.TestCase):
    def test_actual_cli_enter_countdown_and_fake_serial(self):
        self.run_cli(False)

    def test_terminal_termination_sends_stop_and_preserves_failure(self):
        self.run_cli(True)

    def test_mb80_actual_cli_enter_and_fake_serial(self):
        self.run_cli(False, console.MB80_PROFILE)

    def test_mb80_terminal_termination_stops(self):
        self.run_cli(True, console.MB80_PROFILE)

    def run_cli(self, terminate_after_output, profile='standard-50'):
        """真实CLI/TTY+独立伪设备，不枚举或访问任何USB串口。"""
        duty = 80 if profile == console.MB80_PROFILE else 50
        code = console.MB80_APPROVAL_CODE if profile == console.MB80_PROFILE else console.ONE_SHOT_APPROVAL_CODE
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            firmware = root / 'fake.bin'; firmware.write_bytes(b'fake-firmware-only')
            serial_master, serial_slave = pty.openpty()
            keyboard_master, keyboard_slave = pty.openpty()
            writes = []
            stop_simulator = threading.Event()
            simulator_errors = []
            def simulate():
                parser = console.PacketParser()
                state, session, seq = 1, 0, 0
                counts = [0, 0, 0, 0]
                started = False
                next_t = time.monotonic()
                try:
                    while not stop_simulator.is_set():
                        if select.select([serial_master], [], [], .005)[0]:
                            for p in parser.feed(os.read(serial_master, 4096)):
                                now = time.monotonic(); writes.append((now, p)); started = True
                                if p.message_type == console.MSG_STOP: state, session = 1, 0
                                elif p.message_type == console.MSG_HEARTBEAT: session = p.session_id
                                elif p.message_type == console.MSG_ARM: state, session = 2, p.session_id
                                elif p.message_type == console.MSG_M2A_CALIBRATION_HOLD:
                                    ch, direction, duty = struct.unpack('<BbH', p.payload)
                                    if duty: counts[ch] += direction
                                ack = console.Packet(console.MSG_ACK, p.session_id, p.sequence,
                                                     bytes([p.message_type, 0, state, 0]))
                                os.write(serial_master, console.encode_packet(ack))
                        if started and time.monotonic() >= next_t:
                            seq += 1; next_t = time.monotonic() + .05
                            os.write(serial_master, telemetry(seq, state, session, tuple(counts)))
                except BaseException as exc:
                    simulator_errors.append(exc)
            thread = threading.Thread(target=simulate, daemon=True)
            process = None
            output = bytearray()
            try:
                thread.start()
                process = subprocess.Popen([
                    sys.executable, str(TOOL), '--port', os.ttyname(serial_slave),
                    '--channel', 'MB', '--direction', 'plus', '--duty-permille', str(duty),
                    '--max-session-ms', '600', '--trigger-mode', 'one-shot',
                    '--approval-code', code, '--one-shot-profile', profile,
                    '--firmware-bin', str(firmware), '--expected-sha256', console.sha256_file(firmware),
                    '--evidence-root', directory,
                ], stdin=keyboard_slave, stdout=keyboard_slave, stderr=keyboard_slave)
                entered_at = None
                terminated = False
                deadline = time.monotonic() + 12
                while process.poll() is None and time.monotonic() < deadline:
                    if select.select([keyboard_master], [], [], .03)[0]:
                        output.extend(os.read(keyboard_master, 4096))
                    if entered_at is None and '按一次回车'.encode() in output:
                        self.assertEqual(writes, [])
                        entered_at = time.monotonic()
                        os.write(keyboard_master, b'\n')
                    if terminate_after_output and not terminated and any(
                            p.message_type == console.MSG_M2A_CALIBRATION_HOLD
                            and struct.unpack('<BbH', p.payload)[2] for _, p in writes):
                        process.terminate(); terminated = True
                self.assertEqual(process.poll(), 2 if terminate_after_output else 0,
                                 output.decode(errors='replace'))
                self.assertFalse(simulator_errors)
                self.assertIsNotNone(entered_at)
                self.assertGreaterEqual(writes[0][0] - entered_at, 2.95)
                arm = [(t, p) for t, p in writes if p.message_type == console.MSG_ARM]
                self.assertEqual(len(arm), 1)
                nonzero = [(t, p) for t, p in writes if p.message_type == console.MSG_M2A_CALIBRATION_HOLD
                           and struct.unpack('<BbH', p.payload)[2]]
                self.assertGreaterEqual(len(nonzero), 1 if terminate_after_output else 11)
                self.assertTrue(all(struct.unpack('<BbH', p.payload) == (1, 1, duty) for _, p in nonzero))
                record = json.loads(next(root.glob('m2a_run_*/result.json')).read_text())
                self.assertTrue(record['serial_closed'])
                self.assertEqual(record['digital_run_pass'], not terminate_after_output)
                self.assertIn('stop_confirmed_monotonic', record['run_trace'])
                if terminate_after_output:
                    self.assertIn('terminal signal', record['error'])
                    self.assertEqual(writes[-1][1].message_type, console.MSG_STOP)
                else:
                    self.assertTrue(record['stop_confirmed'])
                    self.assertEqual(record['run_trace']['exit_reason'], 'session_limit')
                    self.assertEqual(record['final_telemetry']['state'], 1)
                self.assertLessEqual(record['run_trace']['nonzero_tx_to_stop_attempt_ms'], 605)
            finally:
                if process is not None and process.poll() is None:
                    process.terminate()
                    try: process.wait(timeout=2)
                    except subprocess.TimeoutExpired: process.kill(); process.wait()
                stop_simulator.set(); thread.join(timeout=1)
                for fd in (serial_master, serial_slave, keyboard_master, keyboard_slave): os.close(fd)



class MB80ProfileTests(unittest.TestCase):
    arguments = M2AConsoleTests.arguments
    run_fake = RuntimeTests.run_fake

    def test_exact_profile_and_cross_profile_rejection_before_serial_open(self):
        with tempfile.TemporaryDirectory() as directory:
            firmware = Path(directory) / 'fake.bin'
            firmware.write_bytes(b'offline-only')
            args = self.arguments(firmware, console.sha256_file(firmware))
            args.trigger_mode = 'one-shot'
            args.one_shot_profile = console.MB80_PROFILE
            args.channel, args.direction, args.duty_permille = 'MB', 'plus', 80
            args.approval_code = console.MB80_APPROVAL_CODE
            with mock.patch.object(console.sys.stdin, 'isatty', return_value=True):
                self.assertEqual(console.validate_execution_inputs(args), (1, 1))
                cases = [('channel', x) for x in ('MA', 'MC', 'MD')]
                cases += [('direction', 'minus'), ('trigger_mode', 'hold-space')]
                cases += [('duty_permille', x) for x in (0, 49, 50, 79, 81, 100, 120)]
                cases += [('max_session_ms', x) for x in (0, -1, 601, 850)]
                cases += [('approval_code', x) for x in (console.APPROVAL_CODE, console.ONE_SHOT_APPROVAL_CODE)]
                cases += [('one_shot_profile', x) for x in ('standard-50', 'unknown')]
                for field, value in cases:
                    with self.subTest(field=field, value=value):
                        before = getattr(args, field)
                        setattr(args, field, value)
                        with mock.patch.object(console, 'PosixSerialPort') as port:
                            with self.assertRaises(console.CalibrationConsoleError):
                                console.run_console(args)
                            port.assert_not_called()
                        setattr(args, field, before)
                args.one_shot_profile = 'standard-50'
                args.approval_code = console.ONE_SHOT_APPROVAL_CODE
                for value in (51, 80):
                    args.duty_permille = value
                    with self.assertRaises(console.CalibrationConsoleError):
                        console.validate_execution_inputs(args)

    def test_mb80_single_arm_exact_output_and_stop_deadline(self):
        link, result, error, _ = self.run_fake(mode='one-shot', key=None, profile=console.MB80_PROFILE)
        self.assertIsNone(error)
        holds = [(t, p) for t, p in link.writes if p.message_type == console.MSG_M2A_CALIBRATION_HOLD]
        self.assertGreater(len(holds), 10)
        self.assertTrue(all(struct.unpack('<BbH', p.payload) == (1, 1, 80) for _, p in holds))
        self.assertEqual(sum(p.message_type == console.MSG_ARM for _, p in link.writes), 1)
        self.assertTrue(all(t - link.armed_at <= .600 for t, _ in holds))
        stop = next(t for t, p in link.writes if t > link.armed_at and p.message_type == console.MSG_STOP)
        self.assertLessEqual(stop - link.armed_at, .606)
        self.assertTrue(result['stop_confirmed'])
        self.assertEqual(result['final_telemetry']['state'], console.STATE_DISARMED)

    def test_mb80_faults_cancel_and_stall_do_not_rearm(self):
        for fault in ('crc', 'sequence', 'fault', 'session', 'other_encoder', 'silent',
                      'nack', 'wrong_ack', 'runtime_ack', 'missing_runtime_ack', 'wrong_runtime_command',
                      'missing_stop_ack', 'stop_write', 'interrupt', 'eof_after_output', 'stall',
                      'cancel_after_output'):
            with self.subTest(fault=fault):
                link, result, error, _ = self.run_fake(mode='one-shot', key=None, fault=fault,
                                                     profile=console.MB80_PROFILE)
                self.assertLessEqual(sum(p.message_type == console.MSG_ARM for _, p in link.writes), 1)
                if fault == 'cancel_after_output':
                    self.assertIsNone(error)
                    self.assertTrue(result['stop_confirmed'])
                else:
                    self.assertIsNotNone(error)
                if fault == 'stall':
                    self.assertEqual(sum(p.message_type == console.MSG_M2A_CALIBRATION_HOLD
                                         for _, p in link.writes), 1)

    def test_mb80_cancel_before_enter_never_opens_serial(self):
        with tempfile.TemporaryDirectory() as directory:
            firmware = Path(directory) / 'fake.bin'
            firmware.write_bytes(b'offline-only')
            args = self.arguments(firmware, console.sha256_file(firmware))
            args.trigger_mode, args.one_shot_profile = 'one-shot', console.MB80_PROFILE
            args.channel, args.direction, args.duty_permille = 'MB', 'plus', 80
            args.approval_code = console.MB80_APPROVAL_CODE
            with mock.patch.object(console.sys.stdin, 'isatty', return_value=True), \
                    mock.patch.object(console, '_prepare_one_shot', side_effect=KeyboardInterrupt), \
                    mock.patch.object(console, 'PosixSerialPort') as port, \
                    contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(KeyboardInterrupt):
                    console.run_console(args)
                port.assert_not_called()
            result = json.loads(next(Path(directory).glob('m2a_run_*/result.json')).read_text())
            self.assertFalse(result['serial_opened'])
            self.assertFalse(result['digital_run_pass'])

if __name__ == '__main__':
    unittest.main()
