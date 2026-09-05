#!/usr/bin/env python3
"""无电机双向通信复验：只发成对心跳和STOP，绝不ARM。"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m2a_calibration_console as protocol
from m2a_no_motor_recheck import validate_usb_identity

BURSTS = 60
PERIOD = 0.037
ACK_TIMEOUT = 0.020


def capture(link):
    parser = protocol.CheckedParser()
    session = secrets.randbits(32) or 1
    result = dict(communication_pass=False, heartbeat_acks=0, bursts=0,
                  errors=[], stop_confirmed=False, serial_closed=False)
    telemetry = []
    started = time.monotonic()
    pending = set()
    sent_at = 0.0

    def receive(timeout):
        parser.receive(link, timeout)
        while parser.pending:
            packet = parser.pending.popleft()
            if packet.message_type == protocol.MSG_TELEMETRY:
                t = protocol.decode_telemetry(packet)
                if any(t.encoder_count) or any(t.encoder_delta):
                    raise ValueError('nonzero encoder in no-motor test')
                telemetry.append(asdict(t))
            elif packet.message_type == protocol.MSG_ACK:
                status = protocol.decode_command_status(packet)
                if (status.command_type != protocol.MSG_HEARTBEAT or
                        status.session_id != session or status.sequence not in pending or
                        status.state != protocol.STATE_DISARMED):
                    raise ValueError('unexpected heartbeat ACK')
                if time.monotonic() - sent_at > ACK_TIMEOUT:
                    raise ValueError('late heartbeat ACK')
                pending.remove(status.sequence)
                result['heartbeat_acks'] += 1

    try:
        # 先确认冷启动安全状态，再建立无ARM的心跳会话。
        while not telemetry and time.monotonic() - started < 0.5:
            receive(0.01)
        if not telemetry:
            raise ValueError('initial telemetry missing')
        parser.allowed_sessions = {0, session}
        parser.baseline_counts = (0, 0, 0, 0)
        for burst in range(BURSTS):
            seq = 1 + burst * 2
            pending = {seq, seq + 1}
            frames = b''.join(protocol.encode_packet(protocol.Packet(
                protocol.MSG_HEARTBEAT, session, n)) for n in (seq, seq + 1))
            sent_at = time.monotonic()
            deadline = sent_at + PERIOD
            # 同一次write、紧邻字节流，第二帧会与第一帧ACK的TX重叠。
            link.write(frames, timeout_sec=0.05)
            while time.monotonic() < deadline:
                receive(min(0.005, max(0, deadline - time.monotonic())))
                if pending and time.monotonic() - sent_at > ACK_TIMEOUT:
                    raise ValueError('missing heartbeat ACK')
            if pending:
                raise ValueError('unconfirmed heartbeat pair')
            result['bursts'] += 1
    except BaseException as exc:
        result['errors'].append(f'{type(exc).__name__}: {exc}')
    finally:
        try:
            protocol._send_stop(link)
            parser.allowed_sessions = {0, session}
            t = protocol._confirm_stop(link, parser)
            if any(t.encoder_count) or any(t.encoder_delta):
                raise ValueError('nonzero post-STOP encoder')
            result['stop_confirmed'] = True
            result['final_telemetry'] = asdict(t)
        except BaseException as exc:
            result['errors'].append(f'STOP: {type(exc).__name__}: {exc}')
        finally:
            try:
                link.close()
                result['serial_closed'] = True
            except BaseException as exc:
                result['errors'].append(f'close: {exc}')
    result.update(duration=time.monotonic() - started,
                  telemetry=telemetry, parser_stats=asdict(parser.stats))
    result['communication_pass'] = (not result['errors'] and
        result['bursts'] == BURSTS and result['heartbeat_acks'] == 2 * BURSTS
        and result['stop_confirmed'] and result['serial_closed'])
    return result


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--port', required=True)
    cli.add_argument('--evidence-root', type=Path, required=True)
    cli.add_argument('--confirm-no-motors', action='store_true')
    args = cli.parse_args(argv)
    if not args.confirm_no_motors or not args.evidence_root.is_dir():
        cli.error('需要当次MA-MD全空确认和已存在证据目录')
    from serial.tools import list_ports
    validate_usb_identity(args.port, list_ports.comports())
    output = Path(tempfile.mkdtemp(prefix='uart_duplex_', dir=args.evidence_root))
    result = dict(started_utc=datetime.now(timezone.utc).isoformat(),
                  port=args.port, communication_pass=False,
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with (output / 'serial.jsonl').open('x', encoding='utf-8') as stream:
        try:
            link = protocol.EvidencePort(protocol.PosixSerialPort(args.port, 115200), stream)
        except Exception as exc:
            result.update(errors=[f'open: {exc}'], serial_closed=True)
        else:
            result.update(capture(link))
    result['limitation'] = '仅无电机双向通信，不证明PWM/轮转或M2/H6通过'
    (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != 'telemetry'},
                     ensure_ascii=False, indent=2))
    return 0 if result['communication_pass'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
