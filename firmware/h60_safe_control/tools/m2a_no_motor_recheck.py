#!/usr/bin/env python3
"""M2-A 无电机通信复验；任何错误停止，唯一可发送命令为 STOP。"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'src/p0_base_bridge'))

from p0_base_bridge.h60_protocol import (  # noqa: E402
    MSG_ACK, MSG_STOP, MSG_TELEMETRY, Packet, PacketParser,
    decode_command_status, decode_telemetry, encode_packet,
)
from p0_base_bridge.serial_port import PosixSerialPort  # noqa: E402

STARTUP_SECONDS = 1.0
FORMAL_SECONDS = 3.0
STOP_SECONDS = 0.7
MAX_GAP_SECONDS = 0.25
MAX_RAW_BYTES = 65536
STOP_FRAME = encode_packet(Packet(MSG_STOP))


def validate_usb_identity(port, ports):
    """只核对指定端口，不选择或打开其他端口。"""
    usb = [item for item in ports if item.vid is not None]
    if (len(usb) != 1 or usb[0].device != port or
            (usb[0].vid, usb[0].pid) != (0x1A86, 0x55D4)):
        raise ValueError('USB-COM 身份不符或存在额外 USB 串口；未打开设备')


def telemetry_is_safe(t):
    return (t.state == 1 and t.fault == 0 and t.self_test_ok and
            t.boot_fault_code == 0 and t.session_id == 0 and
            t.firmware_version == (0, 2, 0) and t.capabilities == 2 and
            t.motion_output_available and not any(t.encoder_count) and
            not any(t.encoder_delta))


def capture(link, clock=time.monotonic):
    """接管已确认的 COM；结束时必尝试一次 STOP 并关闭，不重试。"""
    parser = PacketParser()
    raw = bytearray()
    result = {'errors': [], 'events': [], 'packets': [], 'tx': [],
              'windows': {}, 'stop_ack': False, 'serial_closed': False}
    started = clock()
    previous_sequence = None
    last_telemetry_at = None

    def fail(message):
        result['errors'].append(message)

    def window(phase, duration, minimum_frames):
        nonlocal previous_sequence, last_telemetry_at
        beginning = clock()
        count = 0
        before_errors = len(result['errors'])
        initial_stats = asdict(parser.stats)
        try:
            while clock() - beginning < duration:
                remaining = duration - (clock() - beginning)
                chunk = link.read(4096, min(0.05, max(0.0, remaining)))
                now = clock()
                offset = len(raw)
                raw.extend(chunk)
                if len(raw) > MAX_RAW_BYTES:
                    fail(f'{phase}: RX_SIZE_LIMIT')
                    break
                before = asdict(parser.stats)
                packets = parser.feed(chunk)
                result['events'].append({
                    'phase': phase, 'elapsed': now - started,
                    'offset': offset, 'length': len(chunk),
                    'stats': asdict(parser.stats),
                })
                for key in ('crc_errors', 'length_errors', 'version_errors'):
                    if getattr(parser.stats, key) != before[key]:
                        fail(f'{phase}: {key}')
                if phase != 'startup' and parser.stats.discarded_bytes != before['discarded_bytes']:
                    fail(f'{phase}: discarded_bytes')
                for packet in packets:
                    entry = {'phase': phase, 'elapsed': now - started,
                             'type': packet.message_type}
                    if packet.message_type == MSG_TELEMETRY:
                        telemetry = decode_telemetry(packet)
                        entry['telemetry'] = asdict(telemetry)
                        count += 1
                        if not telemetry_is_safe(telemetry):
                            fail(f'{phase}: UNSAFE_TELEMETRY')
                        if (previous_sequence is not None and
                                (telemetry.sequence - previous_sequence) % 2**32 != 1):
                            fail(f'{phase}: SEQUENCE_GAP')
                        reference = last_telemetry_at if last_telemetry_at is not None else beginning
                        if now - reference > MAX_GAP_SECONDS:
                            fail(f'{phase}: TELEMETRY_TIMEOUT')
                        previous_sequence = telemetry.sequence
                        last_telemetry_at = now
                    elif phase == 'stop' and packet.message_type == MSG_ACK:
                        status = decode_command_status(packet)
                        entry['status'] = asdict(status)
                        if (status.command_type == MSG_STOP and status.status == 0 and
                                status.state == 1 and status.fault == 0 and
                                status.session_id == 0 and status.sequence == 0 and
                                not result['stop_ack']):
                            result['stop_ack'] = True
                        else:
                            fail('stop: INVALID_ACK')
                    else:
                        fail(f'{phase}: UNEXPECTED_PACKET_{packet.message_type}')
                    result['packets'].append(entry)
                reference = last_telemetry_at if last_telemetry_at is not None else beginning
                if now - reference > MAX_GAP_SECONDS:
                    fail(f'{phase}: TELEMETRY_TIMEOUT')
                if len(result['errors']) > before_errors:
                    break
        finally:
            result['windows'][phase] = {
                'duration': clock() - beginning, 'telemetry_count': count,
                'stats_before': initial_stats, 'stats_after': asdict(parser.stats),
            }
        if count < minimum_frames:
            fail(f'{phase}: TOO_FEW_FRAMES_{count}')

    try:
        window('startup', STARTUP_SECONDS, 5)
        if not result['errors']:
            window('formal', FORMAL_SECONDS, 25)
    except BaseException as exc:
        fail(f'capture: {type(exc).__name__}: {exc}')
    finally:
        try:
            # 固定字节，不接收调用者提供的任意命令；没有 ARM/心跳/清故障路径。
            result['tx'].append({'command': 'STOP', 'hex': STOP_FRAME.hex(),
                                 'elapsed': clock() - started, 'write_completed': False})
            link.write(STOP_FRAME)
            result['tx'][-1]['write_completed'] = True
            window('stop', STOP_SECONDS, 3)
        except BaseException as exc:
            fail(f'stop: {type(exc).__name__}: {exc}')
        finally:
            try:
                link.close()
                result['serial_closed'] = True
            except BaseException as exc:
                fail(f'close: {type(exc).__name__}: {exc}')
    if not result['stop_ack']:
        fail('stop: ACK_MISSING')
    result['parser_stats'] = asdict(parser.stats)
    result['duration'] = clock() - started
    result['raw_bytes'] = len(raw)
    result['raw_sha256'] = hashlib.sha256(raw).hexdigest()
    result['communication_pass'] = (not result['errors'] and 'formal' in result['windows'])
    result['limitation'] = '仅通信复验；不证明物理零输出、冷启动整批或 M2/H6 通过'
    return result, bytes(raw)


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--port', required=True)
    cli.add_argument('--evidence-root', required=True, type=Path)
    cli.add_argument('--confirm-no-motors', action='store_true')
    args = cli.parse_args(argv)
    if not args.confirm_no_motors:
        cli.error('需要当次现场确认 MA-MD 全空；程序参数不替代真实确认')
    if not args.evidence_root.is_dir():
        cli.error('证据根目录必须已存在')
    from serial.tools import list_ports
    validate_usb_identity(args.port, list_ports.comports())
    output = Path(tempfile.mkdtemp(prefix='no_motor_recheck_', dir=args.evidence_root))
    metadata = {'started_utc': datetime.now(timezone.utc).isoformat(),
                'port': args.port, 'usb_vid_pid': '1A86:55D4',
                'baud_format': '115200 8N1', 'output_directory': str(output)}
    root = Path(__file__).resolve().parents[3]
    metadata['source_sha256'] = {
        relative: hashlib.sha256((root / relative).read_bytes()).hexdigest()
        for relative in (
            'firmware/h60_safe_control/tools/m2a_no_motor_recheck.py',
            'src/p0_base_bridge/p0_base_bridge/h60_protocol.py',
            'src/p0_base_bridge/p0_base_bridge/serial_port.py',
        )
    }
    # 身份与目录检查先于打开；已连接后的所有退出由 capture 负责收尾。
    try:
        link = PosixSerialPort(args.port, 115200)
    except Exception as exc:
        metadata.update(communication_pass=False, errors=[f'open: {exc}'],
                        serial_closed=True, tx=[])
        raw = b''
    else:
        result, raw = capture(link)
        metadata.update(result)
    with (output / 'rx.bin').open('xb') as stream:
        stream.write(raw)
    with (output / 'result.json').open('x', encoding='utf-8') as stream:
        json.dump(metadata, stream, ensure_ascii=False, indent=2)
    print(json.dumps({key: value for key, value in metadata.items()
                      if key not in ('events', 'packets')}, ensure_ascii=False, indent=2))
    return 0 if metadata['communication_pass'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
