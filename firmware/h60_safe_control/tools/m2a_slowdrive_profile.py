"""独立慢衰减候选的固定主机准入；不创建批准，不连接设备。"""
import json
from pathlib import Path

PROFILE = 'mb-plus-50-slow5k-r1'
APPROVAL_CODE = 'M2A-SLOW5K-MB-PLUS-50-ONE-SHOT-REVIEWED'
VERSION = (0, 2, 1)
MANIFEST = (b'P0_H60_SAFE;FW=0.2.1-M2A-SLOW5K-MB-PLUS-50-R1;'
            b'MOTION=1;CAL=0;M2A=1;TIMEOUT_MS=250;UART_RX=IRQ256-R1;'
            b'PWM=SLOW5K-MB-PLUS-50-R1;WAKE_MS=3;STOP=GPIO00\x00')

H6_PROFILE = 'h6-single-wheel-r1'
H6_APPROVAL_CODE = 'H6-SINGLE-WHEEL-ONE-SHOT-REVIEWED'
H6_VERSION = (0, 2, 11)
H6_MANIFEST = (b'P0_H60_SAFE;FW=0.2.11-H6-SINGLE-R1;'
               b'MOTION=1;CAL=0;M2A=1;TIMEOUT_MS=250;UART_RX=IRQ256-R1;'
               b'PWM=H6-SINGLE-5K-R1;WAKE_MS=3;STOP=GPIO00;'
               b'ONE_CHANNEL_PER_ARM=1;MIN_DUTY=50;MAX_DUTY=120;'
               b'HOLD_LEASE_MS=75;MAX_ARMED_MS=1000\x00')
H6_R2_PROFILE = 'h6-single-wheel-r2-mc-plus-80-envelope'
H6_R2_APPROVAL_CODE = 'H6-R2-MC-PLUS-80-ENVELOPE-ONE-SHOT-REVIEWED'
H6_R2_VERSION = (0, 2, 12)
H6_R2_NONZERO_WINDOW_MS = 1800
H6_R2_ABSOLUTE_SESSION_MS = 2500
H6_R2_MANIFEST = (b'P0_H60_SAFE;FW=0.2.12-H6-SINGLE-R2;'
                  b'MOTION=1;CAL=0;M2A=1;TIMEOUT_MS=250;UART_RX=IRQ256-R1;'
                  b'PWM=H6-SINGLE-5K-R2;WAKE_MS=3;STOP=GPIO00;'
                  b'ONE_CHANNEL_PER_ARM=1;MC_PLUS_80_ONLY=1;HOLD_LEASE_MS=75;'
                  b'MAX_ARMED_MS=2500;ENVELOPE_MS=300,1200,300;'
                  b'HOST_NONZERO_MAX_MS=1800\x00')
PROFILES = (PROFILE, H6_PROFILE, H6_R2_PROFILE)


def approval_code(profile):
    if profile == PROFILE:
        return APPROVAL_CODE
    if profile == H6_PROFILE:
        return H6_APPROVAL_CODE
    if profile == H6_R2_PROFILE:
        return H6_R2_APPROVAL_CODE
    raise ValueError('unknown slowdrive profile')


def version(profile):
    if profile == PROFILE:
        return VERSION
    if profile == H6_PROFILE:
        return H6_VERSION
    if profile == H6_R2_PROFILE:
        return H6_R2_VERSION
    raise ValueError('unknown slowdrive profile')


def validate(args):
    profile = args.one_shot_profile
    if profile == PROFILE:
        exact_run = (args.channel == 'MB' and args.direction == 'plus'
                     and args.duty_permille == 50)
        manifest = MANIFEST
        description = 'one-shot MB/plus/50, max 600 ms'
    elif profile == H6_PROFILE:
        exact_run = (args.channel in ('MA', 'MB', 'MC', 'MD')
                     and args.direction in ('plus', 'minus')
                     and 50 <= args.duty_permille <= 120)
        manifest = H6_MANIFEST
        description = 'one-shot one-channel/one-direction/50..120, max 600 ms'
    elif profile == H6_R2_PROFILE:
        exact_run = (args.channel == 'MC' and args.direction == 'plus'
                     and args.duty_permille == 80)
        manifest = H6_R2_MANIFEST
        description = 'one-shot MC/plus/80, exact 1800 ms nonzero window'
    else:
        raise ValueError('unknown slowdrive profile')
    valid_session = (args.max_session_ms == H6_R2_NONZERO_WINDOW_MS
                     if profile == H6_R2_PROFILE
                     else 0 < args.max_session_ms <= 600)
    if (args.trigger_mode != 'one-shot' or not exact_run
            or not valid_session
            or args.approval_code != approval_code(profile)):
        raise ValueError(f'{profile} requires {description}')
    if manifest not in Path(args.firmware_bin).expanduser().read_bytes():
        raise ValueError(f'BIN does not contain the exact {profile} manifest')
    path = Path(args.run_approval).expanduser().resolve()
    record = json.loads(path.read_text())
    expected = dict(approved=True, profile=profile, channel=args.channel,
                    direction=args.direction, duty_permille=args.duty_permille,
                    max_session_ms=args.max_session_ms,
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
