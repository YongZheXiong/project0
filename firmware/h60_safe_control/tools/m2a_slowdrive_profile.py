"""独立慢衰减候选的固定主机准入；不创建批准，不连接设备。"""
import json
from pathlib import Path

PROFILE = 'mb-plus-50-slow5k-r1'
APPROVAL_CODE = 'M2A-SLOW5K-MB-PLUS-50-ONE-SHOT-REVIEWED'
VERSION = (0, 2, 1)
MANIFEST = (b'P0_H60_SAFE;FW=0.2.1-M2A-SLOW5K-MB-PLUS-50-R1;'
            b'MOTION=1;CAL=0;M2A=1;TIMEOUT_MS=250;UART_RX=IRQ256-R1;'
            b'PWM=SLOW5K-MB-PLUS-50-R1;WAKE_MS=3;STOP=GPIO00\x00')


def validate(args):
    if (args.trigger_mode != 'one-shot' or args.channel != 'MB'
            or args.direction != 'plus' or args.duty_permille != 50
            or not 0 < args.max_session_ms <= 600
            or args.approval_code != APPROVAL_CODE):
        raise ValueError('slowdrive requires one-shot MB/plus/50, max 600 ms')
    if MANIFEST not in Path(args.firmware_bin).expanduser().read_bytes():
        raise ValueError('BIN does not contain the exact slowdrive R1 manifest')
    path = Path(args.run_approval).expanduser().resolve()
    record = json.loads(path.read_text())
    expected = dict(approved=True, profile=PROFILE, channel='MB', direction='plus',
                    duty_permille=50, max_session_ms=args.max_session_ms,
                    firmware_sha256=args.expected_sha256.lower())
    if (any(record.get(k) != v for k, v in expected.items())
            or not isinstance(record.get('user_message'), str)
            or not record['user_message'].strip()):
        raise ValueError('missing exact per-run slowdrive approval')
    return path


def consume(args):
    # 独占创建，取消/异常也消费本次入口；不自动重试，不生成新授权。
    path = validate(args)
    with path.with_name(path.name + '.consumed').open('x') as stream:
        stream.write('One invocation consumed; no automatic retry.\n')
