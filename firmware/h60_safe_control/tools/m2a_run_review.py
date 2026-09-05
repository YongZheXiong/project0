"""只读审查既有M2-A日志；不导入设备库，不发送命令，不改写原始记录。"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import stat
import struct
import sys
import zlib


class ReviewError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise ReviewError(message)


def read_file(path):
    require(stat.S_ISREG(path.stat().st_mode), '只接受普通日志文件')
    require(path.stat().st_size <= 4 * 1024 * 1024, '日志超出4MiB短测范围')
    return path.read_bytes()


def parse_json(raw):
    def invalid(value):
        raise ReviewError('JSON含非有限数值: ' + value)
    return json.loads(raw, parse_constant=invalid)


def frames(rows, direction):
    pending = b''
    result = []
    for row in rows:
        if row['direction'] != direction:
            continue
        pending += bytes.fromhex(row['hex'])
        while len(pending) >= 14:
            require(pending[:3] == b'\xa5\x5a\x01', '帧头/版本错误或有丢弃字节')
            size, session, sequence = struct.unpack_from('<HII', pending, 4)
            require(size <= 48, '载荷超过协议上限')
            length = 18 + size
            if len(pending) < length:
                break
            frame, pending = pending[:length], pending[length:]
            require(zlib.crc32(frame[2:-4]) == struct.unpack('<I', frame[-4:])[0],
                    'CRC错误')
            result.append(dict(type=frame[3], session=session, sequence=sequence,
                               payload=frame[14:-4].hex(), time=row['monotonic']))
    require(not pending, '存在未完成帧，不能把残缺日志判为完整')
    return result


def command_signature(items):
    # 会话ID单独报告；比较指令时保留类型、序号与全部载荷。
    return [(f['type'], f['sequence'], f['payload']) for f in items]


def unwrap_delta(channel, current, previous):
    bits = 16 if channel in (1, 3) else 32
    half = 1 << (bits - 1)
    return (current - previous + half) % (1 << bits) - half


def count_metrics(values):
    signs = [1 if d > 0 else -1 for d in values if d]
    pattern = ('NO_CHANGE' if not signs else
               'ONE_DIRECTION_CHANGE' if len(set(signs)) == 1 else 'BIDIRECTIONAL_CHANGE')
    longest = streak = 0
    last = 0
    for delta in values:
        sign = (delta > 0) - (delta < 0)
        streak = streak + 1 if sign and sign == last else int(bool(sign))
        longest = max(longest, streak)
        last = sign
    return dict(net=sum(values), positive=sum(d for d in values if d > 0),
                negative=sum(d for d in values if d < 0), path=sum(abs(d) for d in values),
                nonzero_intervals=len(signs), longest_same_direction_intervals=longest,
                reversals=sum(a != b for a, b in zip(signs, signs[1:])), pattern=pattern)


def review_run(directory):
    directory = Path(directory)
    raw_result = read_file(directory / 'result.json')
    raw_serial = read_file(directory / 'serial.jsonl')
    summary = parse_json(raw_result)
    rows = [parse_json(line) for line in raw_serial.splitlines()]
    require(isinstance(summary, dict) and rows, '缺少结果对象或串口记录')
    previous_time = -1
    for row in rows:
        require(isinstance(row, dict), '日志行不是对象')
        require(row.get('direction') in ('TX_ATTEMPT', 'TX_COMPLETE', 'RX'), '未知记录方向')
        timestamp = row.get('monotonic')
        require(type(timestamp) in (int, float) and math.isfinite(timestamp)
                and timestamp >= previous_time, '日志时间缺失、倒退或非有限')
        previous_time = timestamp
        require(isinstance(row.get('hex'), str), '日志缺少hex字节')
    attempts, tx, rx = [frames(rows, d) for d in ('TX_ATTEMPT', 'TX_COMPLETE', 'RX')]
    require(command_signature(attempts) == command_signature(tx)
            and [f['session'] for f in attempts] == [f['session'] for f in tx],
            '发送尝试与完成不一致')
    require(all(t['time'] >= a['time'] for a, t in zip(attempts, tx)), '发送完成早于尝试')
    require(all(f['type'] in (1, 2, 3, 4, 7) for f in tx), '超出M2-A短测命令范围')
    require(all(f['type'] in (0x80, 0x81, 0x82) for f in rx), '未知响应类型')
    ack = [f for f in rx if f['type'] in (0x81, 0x82)]
    require(len(tx) == len(ack), '命令/ACK数量不匹配')
    issues = []
    for command, response in zip(tx, ack):
        p = bytes.fromhex(response['payload'])
        require(len(p) == 4 and p[0] == command['type']
                and response['session'] == command['session']
                and response['sequence'] == command['sequence'], 'ACK身份或顺序不匹配')
        require(response['time'] >= command['time'], 'ACK早于发送完成')
        if response['type'] != 0x81 or p[1] != 0 or p[3] != 0:
            issues.append('命令被拒绝或ACK报告故障')
    telemetry = []
    for frame in rx:
        if frame['type'] != 0x80:
            continue
        p = bytes.fromhex(frame['payload'])
        require(len(p) == 40, '遥测不是40字节')
        t = dict(sequence=frame['sequence'], session=frame['session'], time=frame['time'],
                 state=p[0], fault=p[1], count=list(struct.unpack_from('<4i', p, 4)),
                 delta=list(struct.unpack_from('<4h', p, 20)),
                 vin_raw=struct.unpack_from('<H', p, 28)[0], version=list(p[32:35]),
                 boot_fault=struct.unpack_from('<I', p, 36)[0])
        require(all(0 <= t['count'][i] <= 65535 for i in (1, 3)), '16位CNT越界')
        if t['fault'] or t['boot_fault'] or p[3] != 1:
            issues.append('遥测故障或自检未通过')
        telemetry.append(t)
    require(len(telemetry) >= 2, '遥测不足，无法比较计数')
    deltas = [[] for _ in range(4)]
    for before, after in zip(telemetry, telemetry[1:]):
        require((after['sequence'] - before['sequence']) % (1 << 32) == 1,
                '遥测序号不连续，不能推算连续计数过程')
        for channel in range(4):
            delta = unwrap_delta(channel, after['count'][channel], before['count'][channel])
            require(abs(delta) < 32767 and after['delta'][channel] == delta,
                    '计数与增量不一致、饱和或跨界歧义')
            deltas[channel].append(delta)
    arm = [f for f in attempts if f['type'] == 2]
    hold = [f for f in attempts if f['type'] == 7]
    require(len(arm) == 1 and hold, '不是一次ARM的M2-A短测')
    decoded_hold = []
    for frame in hold:
        p = bytes.fromhex(frame['payload'])
        require(len(p) == 4, 'HOLD载荷长度错误')
        channel, direction, duty = struct.unpack('<BbH', p)
        require(channel < 4 and direction in (-1, 0, 1) and duty <= 1000,
                'HOLD字段非法')
        decoded_hold.append((channel, direction, duty))
    nonzero = [f for f, (_, direction, duty) in zip(hold, decoded_hold) if direction and duty]
    require(nonzero, '没有非零请求')
    stops = [f for f in attempts if f['type'] == 4 and f['time'] > nonzero[-1]['time']]
    require(stops, '没有输出请求之后的STOP')
    last = telemetry[-1]
    final_stop_acks = [f for f in ack if bytes.fromhex(f['payload'])[0] == 4
                       and f['time'] > stops[0]['time']]
    require(final_stop_acks and last['time'] >= final_stop_acks[0]['time'],
            '缺少末次STOP确认后的遥测')
    if last['state'] != 1 or last['session'] != 0 or any(last['delta']):
        issues.append('末态不是DISARMED/会话0/增量0')
    if summary.get('digital_run_pass') is not True or summary.get('serial_closed') is not True:
        issues.append('原结果未报告数字通过及串口关闭')
    stats = summary.get('parser_stats', {})
    require(isinstance(stats, dict), '解析统计不是对象')
    if any(stats.get(key, 0) for key in
           ('discarded_bytes', 'length_errors', 'version_errors', 'crc_errors')):
        issues.append('原结果报告解析错误或丢弃字节')
    for label, actual in [('initial_telemetry', telemetry[0]), ('final_telemetry', last)]:
        reported = summary.get(label, {})
        require(isinstance(reported, dict), '遥测汇总不是对象')
        require(reported.get('encoder_count') == actual['count']
                and reported.get('sequence') == actual['sequence'], '汇总与原始遥测不一致')
    return dict(run=str(directory.resolve()), hashes={
        'result.json': hashlib.sha256(raw_result).hexdigest(),
        'serial.jsonl': hashlib.sha256(raw_serial).hexdigest()},
        software_identity={k: summary.get(k) for k in
                           ('firmware_sha256', 'console_sha256', 'profile_sha256')},
        digital_audit_pass=not issues, issues=sorted(set(issues)),
        physical_startup='NOT_ASSESSED', physical_direction='NOT_ASSESSED',
        physical_stop='NOT_ASSESSED',
        command_counts=dict(Counter(f['type'] for f in tx)),
        command_signature=command_signature(tx), hold_parameters=sorted(set(decoded_hold)),
        nonzero_to_stop_ms=(stops[0]['time']-nonzero[0]['time'])*1000,
        count_scope='完整采集首末遥测之间；不等同实际PWM输出期间',
        channels={name: count_metrics(values) for name, values in zip(('MA','MB','MC','MD'), deltas)},
        telemetry=telemetry, limits=[
            '数字审查只核验所列日志一致性，不构成新运动授权或完整安全准入。',
            '计数变化只作数字证据；包括连续单向变化，也不自动判物理起转/方向/停车通过。',
            '小幅往返可能来自微动或电气扰动；没有已标定阈值，不设置任意起转PASS门槛。',
            '计数解绕采用相邻采样最短差假设；日志不能排除未观测的半量程以上变化。',
            '命令时刻不是PWM/电流时刻；未校准VIN采样不能排除瞬态。'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path, nargs='+', help='已结束的m2a_run目录（只读）')
    args = parser.parse_args(argv)
    try:
        reports = [review_run(p) for p in args.run]
    except (ReviewError, OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'review_error': str(error), 'digital_audit_pass': False},
                         ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(reports, ensure_ascii=False, indent=2))
    return 0 if all(r['digital_audit_pass'] for r in reports) else 1


if __name__ == '__main__':
    raise SystemExit(main())
