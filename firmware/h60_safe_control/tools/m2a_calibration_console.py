#!/usr/bin/env python3
"""Supervised one-channel M2-A calibration console.

This tool never scans ports and never flashes firmware. Live access requires an
explicit device, the reviewed M2-A BIN and its expected SHA-256. While ARMED it
renews a zero or single-channel 25 ms command lease. The default hold-space
mode requires repeated space events; explicit one-shot mode accepts one ENTER
before a three-second countdown and one bounded session. Terminal loss, any
NACK, fault telemetry, exception, or the absolute session limit sends STOP.
"""

from __future__ import annotations

import argparse
from collections import deque
from dataclasses import asdict
from datetime import datetime, timezone
import json
import tempfile
import hashlib
import os
from pathlib import Path
import secrets
import select
import signal
import sys
import termios
import time
import tty

# 直接脚本运行与测试按文件导入均能找到同目录配置。
sys.path.insert(0, str(Path(__file__).resolve().parent))
import m2a_slowdrive_profile as slowdrive


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BRIDGE_SOURCE = PROJECT_ROOT / "src" / "p0_base_bridge"
sys.path.insert(0, str(BRIDGE_SOURCE))

from p0_base_bridge.h60_protocol import (  # noqa: E402
    CAPABILITY_M2A_CALIBRATION,
    MSG_ACK,
    MSG_ARM,
    MSG_HEARTBEAT,
    MSG_M2A_CALIBRATION_HOLD,
    MSG_NACK,
    MSG_STOP,
    MSG_TELEMETRY,
    Packet,
    PacketParser,
    STATE_ARMED,
    STATE_DISARMED,
    STATUS_OK,
    decode_command_status,
    decode_telemetry,
    encode_m2a_calibration_hold,
    encode_packet,
)
from p0_base_bridge.serial_port import PosixSerialPort  # noqa: E402


APPROVAL_CODE = "M2A-ONE-CHANNEL-REVIEWED"
ONE_SHOT_APPROVAL_CODE = "M2A-ONE-SHOT-REVIEWED"
ONE_SHOT_MAX_SESSION_MS = 600
ONE_SHOT_MAX_DUTY_PERMILLE = 50
MB80_PROFILE = "mb-plus-80"
MB80_APPROVAL_CODE = "M2A-MB-PLUS-80-ONE-SHOT-REVIEWED"
OPERATOR_WAIT_SEC = 300.0
COUNTDOWN_SEC = 3.0
OUTPUT_REFRESH_GAP_SEC = 0.050
RUNTIME_ACK_TIMEOUT_SEC = 0.020
CHANNELS = {"MA": 0, "MB": 1, "MC": 2, "MD": 3}
DIRECTIONS = {"plus": 1, "minus": -1}
MAX_HOST_SESSION_MS = 850
COMMAND_PERIOD_SEC = 0.025
HEARTBEAT_PERIOD_SEC = 0.100
LOCAL_KEY_LEASE_SEC = 0.060
TELEMETRY_TIMEOUT_SEC = 0.250
STOP_CONFIRM_SEC = 0.700


class CalibrationConsoleError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_execution_inputs(args: argparse.Namespace) -> tuple[int, int]:
    mode = getattr(args, 'trigger_mode', 'hold-space')
    profile = getattr(args, 'one_shot_profile', 'standard-50')
    if mode not in ('hold-space', 'one-shot'):
        raise CalibrationConsoleError("unknown trigger mode")
    if profile not in ('standard-50', MB80_PROFILE, slowdrive.PROFILE):
        raise CalibrationConsoleError("unknown one-shot profile")
    required_code = ONE_SHOT_APPROVAL_CODE if mode == 'one-shot' else APPROVAL_CODE
    if profile == slowdrive.PROFILE:
        try:
            slowdrive.validate(args)
        except (ValueError, OSError, AttributeError, TypeError) as exc:
            raise CalibrationConsoleError(f'slowdrive refused: {exc}') from exc
        required_code = slowdrive.APPROVAL_CODE
    if profile == MB80_PROFILE:
        # 本次明确授权仅覆盖左前MB正向80‰；不放宽原50‰模式。
        if (mode != 'one-shot' or args.channel != 'MB'
                or args.direction != 'plus' or args.duty_permille != 80
                or not 0 < args.max_session_ms <= ONE_SHOT_MAX_SESSION_MS):
            raise CalibrationConsoleError("MB80 requires one-shot MB/plus/80 permille, max 600 ms")
        required_code = MB80_APPROVAL_CODE
    if args.approval_code != required_code:
        raise CalibrationConsoleError("missing per-run M2-A approval code")
    if mode == 'one-shot' and profile == 'standard-50' and (args.max_session_ms > ONE_SHOT_MAX_SESSION_MS
                             or args.duty_permille > ONE_SHOT_MAX_DUTY_PERMILLE):
        raise CalibrationConsoleError("one-shot is limited to 50 permille and 600 ms")
    firmware = Path(args.firmware_bin).expanduser().resolve()
    if not firmware.is_file():
        raise CalibrationConsoleError(f"firmware BIN not found: {firmware}")
    expected = args.expected_sha256.lower()
    if len(expected) != 64 or any(char not in "0123456789abcdef" for char in expected):
        raise CalibrationConsoleError("expected SHA-256 must be 64 lowercase hex digits")
    actual = sha256_file(firmware)
    if actual != expected:
        raise CalibrationConsoleError(
            f"firmware SHA-256 mismatch: expected {expected}, got {actual}"
        )
    if args.max_session_ms <= 0 or args.max_session_ms > MAX_HOST_SESSION_MS:
        raise CalibrationConsoleError(
            f"max session must be 1..{MAX_HOST_SESSION_MS} ms"
        )
    if args.duty_permille <= 0 or args.duty_permille > 120:
        raise CalibrationConsoleError("duty must be 1..120 permille")
    if not Path(args.evidence_root).is_dir():
        raise CalibrationConsoleError("evidence root must already exist")
    if not sys.stdin.isatty():
        raise CalibrationConsoleError("interactive TTY is required for operator control")
    return CHANNELS[args.channel], DIRECTIONS[args.direction]


def _operator_key(timeout):
    """直接读终端字节，避免TextIO预读让select与按键缓冲失配。"""
    readable, _, _ = select.select([sys.stdin], [], [], timeout)
    if not readable:
        return None
    data = os.read(sys.stdin.fileno(), 1)
    if not data:
        raise CalibrationConsoleError("terminal input closed")
    return data.decode('ascii', errors='replace')


def _prepare_one_shot(args, trace):
    """只等真实用户输入；回车和倒计时完成以前不打开串口。"""
    old_tty = termios.tcgetattr(sys.stdin.fileno())
    try:
        tty.setcbreak(sys.stdin.fileno())
        print(f"单次 {args.channel}/{args.direction}/{args.duty_permille}‰，"
              f"ARM起算最长{args.max_session_ms}ms。", flush=True)
        print("现场：仅指定电机接入、四轮稳固架空、线束远离轮区；其余设备隔离，"
              "上电轮静止且无异常，主开关随手可达。", flush=True)
        print("确认本批现场条件就绪后按一次回车；随后倒计时3秒，可移开视线观察车轮。"
              "无需空格；其他键取消，运行中q/Ctrl-C停止。", flush=True)
        trace['phase'] = 'waiting_for_enter'
        key = _operator_key(OPERATOR_WAIT_SEC)
        if key not in ('\r', '\n'):
            raise CalibrationConsoleError("operator cancelled or ENTER wait expired")
        trace['operator_enter_monotonic'] = time.monotonic()
        trace['phase'] = 'countdown'
        deadline = time.monotonic() + COUNTDOWN_SEC
        displayed = None
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            number = max(1, int(remaining + 0.999))
            if number != displayed:
                print(number, flush=True)
                displayed = number
            # 连续/重复回车也只会取消，不会创建第二次运行。
            if _operator_key(min(0.05, max(0, remaining))) is not None:
                raise CalibrationConsoleError("operator cancelled during countdown")
        trace['countdown_finished_monotonic'] = time.monotonic()
    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_tty)


class CheckedParser(PacketParser):
    """全程保持同一解析器；任何坏帧或遥测缺口都停止。"""

    def __init__(self, firmware_version=(0, 2, 0)):
        super().__init__()
        self.firmware_version = firmware_version
        self.pending = deque()
        self.latest = None
        self.last_telemetry_at = None
        self.allowed_states = {STATE_DISARMED}
        self.allowed_sessions = {0}
        self.baseline_counts = None
        self.selected_channel = None

    def receive(self, serial_port, timeout):
        before = asdict(self.stats)
        packets = self.feed(serial_port.read(512, timeout))
        for key in ('crc_errors', 'length_errors', 'version_errors', 'discarded_bytes'):
            if getattr(self.stats, key) != before[key]:
                raise CalibrationConsoleError(f"protocol error: {key}")
        now = time.monotonic()
        # 先检查整批，不能在命中应答后漏掉同一 read 的坏帧。
        for packet in packets:
            if packet.message_type == MSG_NACK:
                status = decode_command_status(packet)
                raise CalibrationConsoleError(
                    f"H60 NACK: {status.status_name}; command={status.command_type}, "
                    f"sequence={status.sequence}, fault={status.fault}")
            if packet.message_type == MSG_TELEMETRY:
                t = decode_telemetry(packet)
                if (t.fault_latched or t.boot_fault_code or not t.self_test_ok
                        or not t.motion_output_available
                        or t.firmware_version != self.firmware_version
                        or t.capabilities != CAPABILITY_M2A_CALIBRATION):
                    raise CalibrationConsoleError("unsafe/version-mismatched telemetry")
                if t.state not in self.allowed_states or t.session_id not in self.allowed_sessions:
                    raise CalibrationConsoleError("telemetry state/session changed")
                if self.baseline_counts is not None and any(
                        t.encoder_count[i] != self.baseline_counts[i]
                        for i in range(4) if i != self.selected_channel):
                    raise CalibrationConsoleError("non-selected encoder changed")
                if self.latest is not None and (t.sequence - self.latest.sequence) % 2**32 != 1:
                    raise CalibrationConsoleError("telemetry sequence gap")
                if self.last_telemetry_at is not None and now - self.last_telemetry_at > TELEMETRY_TIMEOUT_SEC:
                    raise CalibrationConsoleError("telemetry timeout")
                self.latest, self.last_telemetry_at = t, now
            elif packet.message_type == MSG_ACK:
                status = decode_command_status(packet)
                if status.status != STATUS_OK or status.fault:
                    raise CalibrationConsoleError("failed ACK status")
            else:
                raise CalibrationConsoleError("unexpected packet type")
        if self.last_telemetry_at is not None and now - self.last_telemetry_at > TELEMETRY_TIMEOUT_SEC:
            raise CalibrationConsoleError("telemetry timeout")
        self.pending.extend(packets)


def _ack_matches(packet, command, session, sequence, state):
    if packet.message_type != MSG_ACK:
        return False
    status = decode_command_status(packet)
    if status.command_type != command:
        return False
    if (status.status != STATUS_OK or status.fault or status.state != state
            or status.session_id != session or status.sequence != sequence):
        raise CalibrationConsoleError("ACK state/session/sequence mismatch")
    return True


def _wait_packet(serial_port, parser, predicate, timeout_sec):
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        while parser.pending:
            packet = parser.pending.popleft()
            if predicate(packet):
                return packet
        parser.receive(serial_port, min(0.02, max(0, deadline - time.monotonic())))
    raise CalibrationConsoleError("timed out waiting for the expected H60 response")


def _confirm_stop(serial_port, parser):
    """仅读取：ACK 后至少两帧 DISARMED、零增量且计数不变。"""
    deadline = time.monotonic() + STOP_CONFIRM_SEC
    ack = False
    last_counts = None
    settled = 0
    # 待处理帧是 STOP 发出前读到的，不能证明本次停车；原始证据仍保留。
    parser.pending.clear()
    while time.monotonic() < deadline:
        parser.receive(serial_port, min(0.02, max(0, deadline - time.monotonic())))
        while parser.pending:
            packet = parser.pending.popleft()
            if packet.message_type == MSG_ACK:
                if _ack_matches(packet, MSG_STOP, 0, 0, STATE_DISARMED):
                    ack = True
            elif packet.message_type == MSG_TELEMETRY and ack:
                t = decode_telemetry(packet)
                if t.state != STATE_DISARMED or t.session_id != 0:
                    raise CalibrationConsoleError("STOP did not leave DISARMED session zero")
                zero = not any(t.encoder_delta)
                settled = settled + 1 if zero and t.encoder_count == last_counts else int(zero)
                last_counts = t.encoder_count
                if settled >= 2:
                    return t
    raise CalibrationConsoleError("STOP ACK or settled post-STOP telemetry missing")


class EvidencePort:
    """先持久化接收字节及发送尝试；不把失败写入伪装成已发送。"""

    def __init__(self, link, stream):
        self.link, self.stream = link, stream
        self.closed = False

    def event(self, direction, data, **extra):
        self.stream.write(json.dumps(dict(direction=direction, hex=data.hex(),
                                         monotonic=time.monotonic(), **extra)) + "\n")
        self.stream.flush()

    def read(self, maximum, timeout):
        data = self.link.read(maximum, timeout)
        if data:
            self.event('RX', data)
        return data

    def write(self, data, timeout_sec=0.05):
        # 日志失败不拦截 STOP；非零命令则必须先成功记录发送意图。
        is_stop = data == encode_packet(Packet(MSG_STOP))
        try:
            self.event('TX_ATTEMPT', data)
        except OSError:
            if not is_stop:
                raise
        self.link.write(data, timeout_sec=timeout_sec)
        self.event('TX_COMPLETE', data)

    def close(self):
        self.link.close()
        self.closed = True


def run_console(args):
    validate_execution_inputs(args)
    if getattr(args, 'one_shot_profile', '') == slowdrive.PROFILE:
        slowdrive.consume(args)
    output = Path(tempfile.mkdtemp(prefix='m2a_run_', dir=args.evidence_root))
    metadata = dict(started_utc=datetime.now(timezone.utc).isoformat(),
                    arguments=vars(args), firmware_sha256=sha256_file(Path(args.firmware_bin)),
                    console_sha256=sha256_file(Path(__file__)), digital_run_pass=False,
                    serial_opened=False, run_trace={})
    if getattr(args, 'one_shot_profile', '') == slowdrive.PROFILE:
        metadata['profile_sha256'] = sha256_file(Path(slowdrive.__file__))
        metadata['approval_sha256'] = sha256_file(Path(args.run_approval).expanduser())
    print(f"Evidence: {output}", flush=True)
    port = None
    operator_tty = None
    old_signals = {}
    trace = metadata['run_trace']
    trace['trigger_mode'] = getattr(args, 'trigger_mode', 'hold-space')
    try:
        if trace['trigger_mode'] == 'one-shot':
            def terminal_signal(signum, _frame):
                raise CalibrationConsoleError(f"terminal signal {signum}")
            for signum in (signal.SIGHUP, signal.SIGTERM):
                old_signals[signum] = signal.signal(signum, terminal_signal)
            _prepare_one_shot(args, trace)
            operator_tty = termios.tcgetattr(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())
        trace['phase'] = 'opening_serial'
        with (output / 'serial.jsonl').open('x', encoding='utf-8') as stream:
            port = EvidencePort(PosixSerialPort(args.port, 115200), stream)
            metadata['serial_opened'] = True
            metadata.update(_run_console(args, port, trace))
            metadata['digital_run_pass'] = True
    except BaseException as exc:
        trace.setdefault('exit_reason', f"{type(exc).__name__}: {exc}")
        metadata['error'] = f"{type(exc).__name__}: {exc}"
        metadata['error_chain'] = []
        cause = exc
        while cause is not None:
            metadata['error_chain'].append(f"{type(cause).__name__}: {cause}")
            cause = cause.__context__
        raise
    finally:
        # 先落盘，再恢复终端；断开的TTY不能阻止保存设备结果。
        metadata['serial_closed'] = port is not None and port.closed
        metadata['limitation'] = '仅数字命令/状态证据；轮位、物理方向与实际停车仍需现场确认'
        try:
            with (output / 'result.json').open('x', encoding='utf-8') as stream:
                json.dump(metadata, stream, ensure_ascii=False, indent=2, default=str)
        finally:
            for signum, previous in old_signals.items():
                signal.signal(signum, previous)
            if operator_tty is not None:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, operator_tty)
        if trace['trigger_mode'] == 'one-shot':
            print("本次已结束，不会自动重试。确认轮停止后拔COM主机端、关主开关、拔电池；"
                  "灯灭后检查支撑、板卡、支架和轮毂。", flush=True)
            print("一次回复：胎顶朝车头/车尾/未动；停止正常/异常；支撑紧固无变化/异常；已断电。",
                  flush=True)


def _send(serial_port: PosixSerialPort, packet: Packet) -> None:
    serial_port.write(encode_packet(packet))


def _send_stop(serial_port: PosixSerialPort) -> None:
    frame = encode_packet(Packet(MSG_STOP))
    for _ in range(3):
        try:
            serial_port.write(frame, timeout_sec=0.05)
        except Exception:
            break


def _check_runtime_packets(parser, session_id, outstanding):
    now = time.monotonic()
    while parser.pending:
        received = parser.pending.popleft()
        if received.message_type == MSG_ACK:
            status = decode_command_status(received)
            expected = outstanding.get(status.sequence)
            if (status.status != STATUS_OK or status.fault or status.state != STATE_ARMED
                    or status.session_id != session_id
                    or expected is None or status.command_type != expected[0]):
                raise CalibrationConsoleError("unexpected runtime ACK")
            if now - expected[1] > RUNTIME_ACK_TIMEOUT_SEC:
                raise CalibrationConsoleError(f"late runtime ACK: sequence={status.sequence}")
            del outstanding[status.sequence]
        elif received.message_type == MSG_TELEMETRY:
            t = decode_telemetry(received)
            if t.state != STATE_ARMED or t.session_id != session_id:
                raise CalibrationConsoleError("runtime state/session changed")
    for sequence, (_, sent_at) in outstanding.items():
        if now - sent_at > RUNTIME_ACK_TIMEOUT_SEC:
            raise CalibrationConsoleError(f"missing runtime ACK: sequence={sequence}")


def _runtime_send_window_open(session_deadline):
    """为已有20ms应答预算留出末尾接收时间，不延长会话或推迟STOP。"""
    return time.monotonic() < session_deadline - RUNTIME_ACK_TIMEOUT_SEC


def _run_console(args, serial_port, trace=None):
    if trace is None:
        trace = {}
    one_shot = getattr(args, 'trigger_mode', 'hold-space') == 'one-shot'
    trace.update(trigger_mode='one-shot' if one_shot else 'hold-space',
                 nonzero_commands=0, stop_confirmed=False)
    channel, direction = CHANNELS[args.channel], DIRECTIONS[args.direction]
    firmware_version = (slowdrive.VERSION if getattr(args, 'one_shot_profile', '')
                        == slowdrive.PROFILE else (0, 2, 0))
    parser = CheckedParser(firmware_version)
    session_id = secrets.randbits(32) or 1
    sequence = 1
    old_tty = None
    latest_telemetry = None
    initial_telemetry = None
    final_telemetry = None
    stop_confirmed = False
    had_output = False
    last_nonzero_tx = None
    outstanding = {}

    try:
        _send_stop(serial_port)
        packet = _wait_packet(
            serial_port,
            parser,
            lambda item: item.message_type == MSG_TELEMETRY,
            2.0,
        )
        latest_telemetry = decode_telemetry(packet)
        initial_telemetry = latest_telemetry
        trace['initial_telemetry'] = asdict(initial_telemetry)
        if latest_telemetry.session_id != 0 or latest_telemetry.state != STATE_DISARMED:
            raise CalibrationConsoleError("H60 did not report DISARMED")
        if not latest_telemetry.self_test_ok or not latest_telemetry.motion_output_available:
            raise CalibrationConsoleError("H60 self-test or motion gate is not ready")
        if latest_telemetry.firmware_version != firmware_version:
            raise CalibrationConsoleError(f"H60 firmware is not numeric version {firmware_version}")
        if not latest_telemetry.capabilities & CAPABILITY_M2A_CALIBRATION:
            raise CalibrationConsoleError("H60 does not report the M2-A capability")

        if any(latest_telemetry.encoder_delta):
            raise CalibrationConsoleError("encoder motion before ARM")
        parser.baseline_counts = latest_telemetry.encoder_count
        parser.selected_channel = channel
        parser.allowed_sessions = {0, session_id}
        heartbeat = Packet(MSG_HEARTBEAT, session_id, sequence)
        _send(serial_port, heartbeat)
        _wait_packet(
            serial_port,
            parser,
            lambda item: _ack_matches(item, MSG_HEARTBEAT, session_id, sequence, STATE_DISARMED),
            0.5,
        )
        sequence += 1

        if one_shot and _operator_key(0.0) is not None:
            raise CalibrationConsoleError("operator cancelled before ARM")
        parser.allowed_sessions = {session_id}
        parser.allowed_states = {STATE_DISARMED, STATE_ARMED}
        arm = Packet(MSG_ARM, session_id, sequence)
        armed_at = time.monotonic()
        session_deadline = armed_at + args.max_session_ms / 1000.0
        trace['arm_attempt_monotonic'] = armed_at
        trace['phase'] = 'arming'
        _send(serial_port, arm)
        _wait_packet(
            serial_port,
            parser,
            lambda item: _ack_matches(item, MSG_ARM, session_id, sequence, STATE_ARMED),
            0.25,
        )
        sequence += 1
        _wait_packet(
            serial_port,
            parser,
            lambda item: item.message_type == MSG_TELEMETRY
            and decode_telemetry(item).state == STATE_ARMED
            and item.session_id == session_id,
            0.25,
        )

        parser.allowed_states = {STATE_ARMED}
        print(f"ARMED {args.channel} {args.direction} at {args.duty_permille} permille. "
              + ("单次运行中，请观察车轮；到时自动停止。" if one_shot else
                 "Hold SPACE to renew output; release SPACE or press q to stop."), flush=True)
        if not one_shot:
            old_tty = termios.tcgetattr(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())
        key_deadline = 0.0
        next_command = time.monotonic()
        next_heartbeat = time.monotonic()
        trace['phase'] = 'running'
        trace['exit_reason'] = 'session_limit'

        while (time.monotonic() - armed_at) * 1000.0 < args.max_session_ms:
            now = time.monotonic()
            key = _operator_key(min(0.005, max(0.0, armed_at + args.max_session_ms / 1000 - now)))
            now = time.monotonic()
            if key is not None:
                if one_shot:
                    trace['exit_reason'] = 'operator_key'
                    break
                if key == " ":
                    key_deadline = now + LOCAL_KEY_LEASE_SEC
                elif key in ("q", "Q", "\x03", "\x1b"):
                    trace['exit_reason'] = 'operator_key'
                    break

            if not one_shot and had_output and now > key_deadline:
                trace['exit_reason'] = 'key_lease_expired'
                break
            if last_nonzero_tx is not None and now - last_nonzero_tx > OUTPUT_REFRESH_GAP_SEC:
                raise CalibrationConsoleError("output refresh delayed; refusing to resume")
            if (time.monotonic() - armed_at) * 1000 >= args.max_session_ms:
                break

            # 先处理已到达的坏帧/异常状态，不能在检查前再续租输出。
            parser.receive(serial_port, 0.0)
            _check_runtime_packets(parser, session_id, outstanding)

            if now >= next_heartbeat and _runtime_send_window_open(session_deadline):
                outstanding[sequence] = (MSG_HEARTBEAT, time.monotonic())
                _send(serial_port, Packet(MSG_HEARTBEAT, session_id, sequence))
                sequence += 1
                next_heartbeat = now + HEARTBEAT_PERIOD_SEC

            if now >= next_command and _runtime_send_window_open(session_deadline):
                if (time.monotonic() - armed_at) * 1000 >= args.max_session_ms:
                    break
                if last_nonzero_tx is not None and time.monotonic() - last_nonzero_tx > OUTPUT_REFRESH_GAP_SEC:
                    raise CalibrationConsoleError("output refresh delayed; refusing to resume")
                active = one_shot or time.monotonic() <= key_deadline
                had_output = had_output or active
                payload = encode_m2a_calibration_hold(
                    channel,
                    direction if active else 0,
                    args.duty_permille if active else 0,
                )
                outstanding[sequence] = (MSG_M2A_CALIBRATION_HOLD, time.monotonic())
                _send(
                    serial_port,
                    Packet(MSG_M2A_CALIBRATION_HOLD, session_id, sequence, payload),
                )
                if active:
                    last_nonzero_tx = time.monotonic()
                    trace.setdefault('first_nonzero_tx_monotonic', last_nonzero_tx)
                    trace['last_nonzero_tx_monotonic'] = last_nonzero_tx
                    trace['nonzero_commands'] += 1
                sequence += 1
                next_command = now + COMMAND_PERIOD_SEC

            parser.receive(serial_port, 0.0)
            _check_runtime_packets(parser, session_id, outstanding)
        parser.receive(serial_port, 0.0)
        _check_runtime_packets(parser, session_id, outstanding)
        if outstanding:
            raise CalibrationConsoleError("runtime ended with unconfirmed commands")
    except BaseException as exc:
        trace['exit_reason'] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        try:
            trace['phase'] = 'stopping'
            trace['stop_attempt_monotonic'] = time.monotonic()
            if 'first_nonzero_tx_monotonic' in trace:
                trace['nonzero_tx_to_stop_attempt_ms'] = (
                    trace['stop_attempt_monotonic'] - trace['first_nonzero_tx_monotonic']) * 1000
            _send_stop(serial_port)
            parser.allowed_states = {STATE_DISARMED, STATE_ARMED}
            parser.allowed_sessions = {0, session_id}
            final_telemetry = _confirm_stop(serial_port, parser)
            stop_confirmed = True
            trace['stop_confirmed'] = True
            trace['final_telemetry'] = asdict(final_telemetry)
            trace['stop_confirmed_monotonic'] = time.monotonic()
            trace['phase'] = 'stopped'
        finally:
            try:
                if old_tty is not None:
                    termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_tty)
            finally:
                serial_port.close()
                trace['serial_closed_monotonic'] = time.monotonic()
    if stop_confirmed:
        print("STOP acknowledged; post-STOP encoder counts: "
              + ", ".join(str(value) for value in final_telemetry.encoder_count))
    return dict(session_id=session_id, channel=args.channel, direction=args.direction,
                duty_permille=args.duty_permille, output_requested=had_output, initial_telemetry=asdict(initial_telemetry),
                final_telemetry=asdict(final_telemetry), stop_confirmed=stop_confirmed,
                parser_stats=asdict(parser.stats), run_trace=trace)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Supervised H60 M2-A one-channel deadman calibration"
    )
    parser.add_argument("--port", required=True, help="explicit USB-COM device")
    parser.add_argument("--channel", required=True, choices=tuple(CHANNELS))
    parser.add_argument("--direction", required=True, choices=tuple(DIRECTIONS))
    parser.add_argument("--duty-permille", type=int, default=50, choices=range(1, 121))
    parser.add_argument("--max-session-ms", type=int, default=600)
    parser.add_argument("--trigger-mode", choices=('hold-space', 'one-shot'), default='hold-space',
                        help="one-shot requires its own approval code and an operator ENTER/countdown")
    parser.add_argument("--one-shot-profile", choices=('standard-50', MB80_PROFILE, slowdrive.PROFILE),
                        default='standard-50', help="explicit per-run reviewed profile")
    parser.add_argument("--firmware-bin", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--approval-code", required=True)
    parser.add_argument("--run-approval", help="slowdrive only: exact per-run approval JSON")
    parser.add_argument("--evidence-root", required=True, help="existing evidence directory")
    return parser


def main() -> int:
    try:
        run_console(build_parser().parse_args())
    except (CalibrationConsoleError, OSError, ValueError, KeyboardInterrupt) as exc:
        print(f"M2-A refused/stopped: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
