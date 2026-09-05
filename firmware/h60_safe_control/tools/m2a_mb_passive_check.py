#!/usr/bin/env python3
"""仅 M1/MB 已连接时的静止遥测检查；不发送任何协议命令。"""

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/p0_base_bridge'))
from p0_base_bridge.h60_protocol import MSG_TELEMETRY, PacketParser, decode_telemetry
from p0_base_bridge.serial_port import PosixSerialPort


def capture(link, clock=time.monotonic):
    """有限时读取，关闭串口；出错只能要求现场断电，不能软件驱动。"""
    parser = PacketParser()
    raw = bytearray()
    result = dict(errors=[], events=[], telemetry=[], tx=[], serial_closed=False)
    started = clock()
    last_at = started
    previous = None
    baseline = None
    formal_frames = 0
    try:
        while clock() - started < 4.0:
            chunk = link.read(4096, min(0.05, 4.0 - (clock() - started)))
            now = clock()
            before = asdict(parser.stats)
            offset = len(raw)
            raw.extend(chunk)
            result['events'].append(dict(elapsed=now-started, offset=offset, length=len(chunk)))
            if len(raw) > 65536:
                raise ValueError('RX_SIZE_LIMIT')
            packets = parser.feed(chunk)
            for key in ('crc_errors', 'length_errors', 'version_errors'):
                if getattr(parser.stats, key) != before[key]:
                    raise ValueError(key)
            # 首秒只容许接入时的残片丢弃；坏帧和全部原始字节仍保留。
            if now-started >= 1.0 and parser.stats.discarded_bytes != before['discarded_bytes']:
                raise ValueError('discarded_bytes')
            for packet in packets:
                if packet.message_type != MSG_TELEMETRY:
                    raise ValueError('UNEXPECTED_PACKET')
                t = decode_telemetry(packet)
                result['telemetry'].append(dict(elapsed=now-started, **asdict(t)))
                if (t.state != 1 or t.session_id != 0 or t.fault or t.boot_fault_code
                        or not t.self_test_ok or not t.motion_output_available
                        or t.firmware_version != (0, 2, 0) or t.capabilities != 2):
                    raise ValueError('UNSAFE_TELEMETRY')
                if any(t.encoder_delta) or any(t.encoder_count[i] for i in (0, 2, 3)):
                    raise ValueError('ENCODER_ACTIVITY_OR_UNCONNECTED_COUNT')
                counts = tuple(t.encoder_count)
                if baseline is None:
                    baseline = counts
                if counts != baseline:
                    raise ValueError('ENCODER_COUNT_CHANGED')
                if previous is not None and (t.sequence-previous) % 2**32 != 1:
                    raise ValueError('SEQUENCE_GAP')
                if now-last_at > 0.25:
                    raise ValueError('TELEMETRY_TIMEOUT')
                previous, last_at = t.sequence, now
                if now-started >= 1.0:
                    formal_frames += 1
            if now-last_at > 0.25:
                raise ValueError('TELEMETRY_TIMEOUT')
        if formal_frames < 25:
            raise ValueError('TOO_FEW_FORMAL_FRAMES')
    except BaseException as exc:
        result['errors'].append(f'{type(exc).__name__}: {exc}')
    finally:
        try:
            link.close()
            result['serial_closed'] = True
        except BaseException as exc:
            result['errors'].append(f'close: {exc}')
    result.update(duration=clock()-started, formal_frames=formal_frames,
                  parser_stats=asdict(parser.stats), raw_sha256=hashlib.sha256(raw).hexdigest(),
                  passive_check_pass=not result['errors'],
                  limitation='只证明该窗口的数字静止状态；物理轮静止由用户观察，不构成运动或电气零输出验收')
    return result, bytes(raw)


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--port', required=True)
    cli.add_argument('--evidence-root', required=True, type=Path)
    cli.add_argument('--confirm-only-m1-mb-powered-stationary', action='store_true')
    args = cli.parse_args(argv)
    if not args.confirm_only_m1_mb_powered_stationary:
        cli.error('须当次确认仅M1接MB、H60已上电且轮静止；参数不替代现场确认')
    if not args.evidence_root.is_dir():
        cli.error('证据根目录必须已存在')
    from serial.tools import list_ports
    usb = [p for p in list_ports.comports() if p.vid is not None]
    if (len(usb) != 1 or usb[0].device != args.port
            or (usb[0].vid, usb[0].pid) != (0x1A86, 0x55D4)):
        cli.error('USB-COM身份不符或有额外USB串口，未打开设备')
    output = Path(tempfile.mkdtemp(prefix='mb_passive_', dir=args.evidence_root))
    metadata = dict(started_utc=datetime.now(timezone.utc).isoformat(), port=args.port,
                    topology='M1/左前→MB；MA/MC/MD空；USB-COM运行接口', tx=[],
                    source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in (Path(__file__).resolve(),
                                             ROOT/'src/p0_base_bridge/p0_base_bridge/h60_protocol.py',
                                             ROOT/'src/p0_base_bridge/p0_base_bridge/serial_port.py')})
    try:
        link = PosixSerialPort(args.port, 115200)
    except Exception as exc:
        raw = b''
        metadata.update(passive_check_pass=False, errors=[f'open: {exc}'])
    else:
        result, raw = capture(link)
        metadata.update(result)
    (output/'rx.bin').write_bytes(raw)
    (output/'result.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(output=str(output), passed=metadata['passive_check_pass'],
                          errors=metadata['errors']), ensure_ascii=False))
    return 0 if metadata['passive_check_pass'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
