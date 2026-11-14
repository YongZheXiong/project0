"""隔离ROS回放台架；只启动真实适配/仲裁节点，不导入底座桥或打开input。"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

PLAN_ID = 'NANO-ROS-REPLAY-20261011-01'
NAMESPACE = '/project0_ros_replay_01'
DOMAIN = '188'
REMAPS = {name: NAMESPACE + name for name in (
    '/joy', '/p0/manual/cmd_vel', '/p0/navigation/cmd_vel',
    '/p0/base/status', '/p0/base/cmd_vel', '/p0/motion/stop',
    '/p0/motion/clear_lock')}
SCOPE = dict(ros_replay=True, fixture_mapping_only=True, substitute_base=True,
             physical_input=False, serial=False, real_base_bridge=False,
             services_or_system_config=False, motion=False)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)


def verify_package(root):
    plan_path = root / 'plan.json'
    plan = json.loads(plan_path.read_text())
    if plan['id'] != PLAN_ID or plan['scope'] != SCOPE:
        raise ValueError('PLAN_SCOPE')
    for name, digest in plan['files'].items():
        path = root / name
        if Path(name).is_absolute() or '..' in Path(name).parts or path.is_symlink():
            raise ValueError('UNSAFE_MANIFEST_PATH')
        if sha(path) != digest:
            raise ValueError('FROZEN_SOURCE_DRIFT ' + name)
    auth = json.loads((root / 'authorization.json').read_text())
    if (auth.get('approved') is not True or auth.get('plan_id') != PLAN_ID
            or auth.get('plan_sha256') != sha(plan_path)
            or auth.get('scope') != SCOPE or not auth.get('source_text')
            or not auth.get('source_thread') or not auth.get('approved_at')):
        raise ValueError('NEW_SPECIFIC_AUTHORIZATION_REQUIRED')
    if (root / 'started.json').exists():
        raise ValueError('PACKAGE_CONSUMED_NO_REPLAY')
    return plan


def preflight(plan):
    """只读身份/进程/USB检查，不打开端点，不推断物理断电。"""
    serial = Path('/proc/device-tree/serial-number').read_bytes()
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    if hashlib.sha256(serial).hexdigest() != plan['serial_sha256'] or boot != plan['boot']:
        raise ValueError('BOARD_OR_BOOT_CHANGED_REVIEW_REQUIRED')
    if os.environ.get('ROS_DOMAIN_ID') != DOMAIN or os.environ.get('ROS_LOCALHOST_ONLY') != '1':
        raise ValueError('DDS_ISOLATION_REQUIRED')
    for usb in Path('/sys/bus/usb/devices').glob('*'):
        vid, pid = usb / 'idVendor', usb / 'idProduct'
        if vid.exists() and pid.exists() and vid.read_text().strip() == '1a86' and pid.read_text().strip() == '55d4':
            raise ValueError('H60_USB_PRESENT')
    for proc in Path('/proc').glob('[0-9]*/cmdline'):
        if proc.parent.name == str(os.getpid()):
            continue
        try:
            arguments = proc.read_bytes().decode(errors='replace').split('\0')
        except (FileNotFoundError, ProcessLookupError):
            continue
        # 匹配真实argv单元，避免把预检父shell内嵌的计划/源码字符串误判为控制进程。
        modules = {'p0_base_bridge', 'p0_manual_control', 'p0_safety_manager', 'p0_linux_joy',
                   'p0_base_bridge.node', 'p0_manual_control.node',
                   'p0_manual_control.linux_joy_node', 'p0_safety_manager.node'}
        executables = {'base_bridge', 'joy_adapter', 'linux_joy', 'command_arbiter'}
        if any(arg in modules or (len(arg) < 512 and arg.rsplit('/', 1)[-1] in executables)
               for arg in arguments):
            raise ValueError('OTHER_CONTROL_PROCESS_PRESENT')
    return dict(boot=boot, serial_sha256=hashlib.sha256(serial).hexdigest(),
                h60_usb_absent=True, other_control_process_absent=True)


@dataclass(frozen=True)
class Phase:
    name: str
    input_name: str | None
    expected: tuple[float, float, bool]
    comm: bool = True
    ready: bool = True
    action: str = ''
    manual_expected: tuple[float, float, bool] | None = None


ZERO = (0.0, 0.0, False)


def phases(fixture):
    """方向期望取自人工标签；计算独立于生产map_joy。"""
    def expected(name):
        row = fixture['inputs'][name]
        linear, angular = row['axes'][1], row['axes'][3]
        return (-0.2 * linear if abs(linear) > 0.10 else 0.0,
                -0.8 * angular if abs(angular) > 0.10 else 0.0, True)
    forward, backward, left, right = (expected(x) for x in ('forward', 'backward', 'left', 'right'))
    return [
        Phase('mapping_guard', 'forward', ZERO),
        Phase('neutral', 'neutral', ZERO, action='fixture_mapping'),
        Phase('forward', 'forward', forward),
        Phase('backward', 'backward', backward),
        Phase('left', 'left', left),
        Phase('right', 'right', right),
        Phase('deadman_release', 'released', ZERO),
        Phase('comm_gate', 'forward', ZERO, comm=False, manual_expected=forward),
        Phase('base_ready_gate', 'forward', ZERO, ready=False, manual_expected=forward),
        Phase('fresh_resume', 'forward', forward),
        Phase('joy_timeout', None, ZERO),
        Phase('neutral_after_timeout', 'neutral', ZERO),
        Phase('fresh_after_timeout', 'forward', forward),
        Phase('software_lock', 'forward', ZERO, action='lock', manual_expected=forward),
        Phase('drain_joy_before_clear', None, ZERO),
        Phase('clear_without_fresh_joy', None, ZERO, action='clear'),
        Phase('fresh_after_clear', 'forward', forward, action='neutral_then_fresh'),
        Phase('manual_publisher_timeout', None, ZERO, action='remove_adapter'),
    ]


def assess(phase, rows):
    """忽略最多0.60秒转换期；稳定窗口任何坏帧/缺流/大间隙均拒绝。"""
    checked = {}
    for stream in ('manual', 'base'):
        selected = [r for r in rows if r['stream'] == stream and r['elapsed'] >= 0.60]
        if phase.action == 'remove_adapter' and stream == 'manual':
            if selected:
                raise ValueError('ADAPTER_STILL_PUBLISHING')
            continue
        target = phase.expected if stream == 'base' else (phase.manual_expected or phase.expected)
        if len(selected) < 5:
            raise ValueError('MISSING_OUTPUT ' + phase.name + ' ' + stream)
        if selected[0]['elapsed'] > 0.80 or selected[-1]['elapsed'] < 1.0:
            raise ValueError('INCOMPLETE_STABLE_WINDOW')
        if any(b['elapsed'] - a['elapsed'] > 0.25 for a, b in zip(selected, selected[1:])):
            raise ValueError('OUTPUT_STALL')
        for row in selected:
            if (row['active'] != target[2] or not all(math.isfinite(row[k]) and
                    abs(row[k] - v) <= 0.001 for k, v in zip(('linear', 'angular'), target[:2]))):
                raise ValueError('UNEXPECTED_OUTPUT ' + phase.name + ' ' + stream)
            if stream == 'base' and row['source'] != ('manual' if target[2] else 'safety'):
                raise ValueError('UNEXPECTED_ARBITRATION_SOURCE')
        checked[stream] = len(selected)
    return dict(phase=phase.name, status='PASS_STABLE_WINDOW', samples=checked,
                settle_seconds=0.60, physical_stop_timing_verified=False)


def run_ros(root, fixture):
    """此函数只能在新批准/真实门之后运行；真实ROS运行结果与离线替身分列。"""
    import rclpy
    from rclpy.executors import SingleThreadedExecutor
    from rclpy.parameter import Parameter
    from sensor_msgs.msg import Joy
    from p0_interfaces.msg import ChassisCmd, ChassisStatus
    from p0_interfaces.srv import StopMotion, ClearMotionLock
    from p0_manual_control.node import ManualControlNode
    from p0_safety_manager.node import SafetyManagerNode

    args = ['--ros-args', '-r', '__ns:=' + NAMESPACE]
    for original, isolated in REMAPS.items():
        args.extend(['-r', original + ':=' + isolated])
    rclpy.init(args=args)
    observer = adapter = safety = None
    executor = SingleThreadedExecutor()
    rows, reports, graph = [], [], []
    phase_start = time.monotonic()
    current_phase = 'startup'
    adapter_removed = False
    with (root / 'outputs.jsonl').open('x') as output:
        try:
            observer = rclpy.create_node('replay_observer')
            executor.add_node(observer)
            # 等待发现已有图；发现同domain任何其他节点均拒绝，不连接生产图。
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                executor.spin_once(timeout_sec=0.05)
                names = observer.get_node_names_and_namespaces()
                if any((n, ns) != ('replay_observer', NAMESPACE) for n, ns in names):
                    raise ValueError('DDS_DOMAIN_ALREADY_OCCUPIED')
            adapter = ManualControlNode()
            safety = SafetyManagerNode()
            executor.add_node(adapter)
            executor.add_node(safety)
            joy_pub = observer.create_publisher(Joy, '/joy', 10)
            status_pub = observer.create_publisher(ChassisStatus, '/p0/base/status', 10)
            def record(stream, message):
                row = dict(phase=current_phase, elapsed=time.monotonic() - phase_start,
                           stream=stream, active=bool(message.active),
                           linear=float(message.linear_x_mps), angular=float(message.angular_z_radps),
                           source=message.source, sequence=int(message.sequence))
                rows.append(row)
                output.write(json.dumps(row) + '\n')
                output.flush()
            observer.create_subscription(ChassisCmd, '/p0/manual/cmd_vel', lambda m: record('manual', m), 10)
            observer.create_subscription(ChassisCmd, '/p0/base/cmd_vel', lambda m: record('base', m), 10)
            clients = {
                'lock': (observer.create_client(StopMotion, '/p0/motion/stop'), StopMotion),
                'clear': (observer.create_client(ClearMotionLock, '/p0/motion/clear_lock'), ClearMotionLock),
            }
            # 发现节点和所有测试连接，避免把未建立DDS连接当功能失败。
            deadline = time.monotonic() + 6.0
            while True:
                executor.spin_once(timeout_sec=0.05)
                names = sorted(observer.get_node_names_and_namespaces())
                graph.append(dict(at=time.monotonic(), names=names))
                expected_names = sorted((n, NAMESPACE) for n in
                                        ('replay_observer', 'p0_manual_control', 'p0_safety_manager'))
                if (names == expected_names and joy_pub.get_subscription_count() == 1
                        and status_pub.get_subscription_count() == 1
                        and adapter._publisher.get_subscription_count() == 2
                        and safety._publisher.get_subscription_count() == 1
                        and all(c.service_is_ready() for c, _ in clients.values())):
                    break
                if time.monotonic() > deadline:
                    raise ValueError('GRAPH_OR_CONNECTIONS_MISSING')
            topics = {name for name, _ in observer.get_topic_names_and_types()}
            if not topics.issubset(set(REMAPS.values()) | {'/rosout', '/parameter_events'}):
                raise ValueError('UNISOLATED_TOPIC_PRESENT')
            for phase in phases(fixture):
                current_phase = phase.name
                print('ROS回放阶段：' + current_phase, flush=True)
                if phase.action == 'fixture_mapping':
                    parameters = dict(mapping_confirmed=True, linear_axis=1, angular_axis=3,
                                      deadman_button=5, linear_scale=-0.2, angular_scale=-0.8)
                    results = adapter.set_parameters([Parameter(k, value=v) for k, v in parameters.items()])
                    if not all(r.successful for r in results):
                        raise ValueError('FIXTURE_PARAMETER_REJECTED')
                elif phase.action in clients:
                    client, service = clients[phase.action]
                    request = service.Request()
                    if phase.action == 'lock':
                        request.reason = 'isolated_replay_fixture'
                    future = client.call_async(request)
                    deadline = time.monotonic() + 2.0
                    while not future.done() and time.monotonic() < deadline:
                        executor.spin_once(timeout_sec=0.02)
                    if not future.done() or not future.result().success:
                        raise ValueError('FIXTURE_SERVICE_FAILED')
                elif phase.action == 'remove_adapter':
                    executor.remove_node(adapter)
                    adapter.destroy_node()
                    adapter_removed = True
                phase_start = time.monotonic()
                first_row = len(rows)
                next_publish = phase_start
                while time.monotonic() - phase_start < 1.20:
                    now = time.monotonic()
                    if now >= next_publish:
                        status = ChassisStatus()
                        status.comm_ok, status.motion_ready = phase.comm, phase.ready
                        status_pub.publish(status)
                        if phase.input_name is not None:
                            # 输入超时后必须先回中且松开使能；保持清锁阶段本身无新Joy。
                            input_name = ('neutral' if phase.action == 'neutral_then_fresh'
                                          and now - phase_start < 0.20 else phase.input_name)
                            data = fixture['inputs'][input_name]
                            joy = Joy()
                            joy.header.stamp = observer.get_clock().now().to_msg()
                            joy.header.frame_id = 'recorded_or_synthetic_fixture_only'
                            joy.axes, joy.buttons = data['axes'], data['buttons']
                            joy_pub.publish(joy)
                        next_publish = now + 0.04
                    executor.spin_once(timeout_sec=0.005)
                reports.append(assess(phase, rows[first_row:]))
            return reports
        finally:
            save(root / 'graph.json', graph)
            if adapter is not None and not adapter_removed:
                executor.remove_node(adapter)
                adapter.destroy_node()
            for node in (safety, observer):
                if node is not None:
                    executor.remove_node(node)
                    node.destroy_node()
            executor.shutdown()
            if rclpy.ok():
                rclpy.shutdown()
            save(root / 'ros_cleanup.json', dict(all_owned_nodes_destroyed=True,
                                                serial_or_input_opened=False,
                                                python_version=sys.version))


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--package', type=Path, required=True)
    args = cli.parse_args()
    root = args.package.resolve()
    plan = verify_package(root)
    save(root / 'preflight.json', preflight(plan))
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise ValueError('VISIBLE_TERMINAL_REQUIRED')
    print('NANO_ROS_REPLAY01_READY：确认Nano原适配器/散热正常；H60断电且COM/DEBUG拔除；雷达断电。只回放，不操作手柄。', flush=True)
    with (root / 'gate_attempts.jsonl').open('x') as log:
        while True:
            answer = input('输入READY_ROS_REPLAY，异常输入ANOMALY，取消输入CANCEL：').strip()
            log.write(json.dumps(dict(at=time.time(), answer=answer)) + '\n'); log.flush()
            if answer in ('CANCEL', 'ANOMALY'):
                return 2
            if answer == 'READY_ROS_REPLAY':
                break
    # 真实门后再检查当前身份/进程/USB；此后才导入ROS并消费本包。
    preflight(plan)
    save(root / 'started.json', dict(plan=PLAN_ID, at=time.time()))
    for package in ('p0_manual_control', 'p0_safety_manager'):
        sys.path.insert(0, str(root / 'src' / package))
    try:
        report = run_ros(root, json.loads((root / 'fixture.json').read_text()))
        save(root / 'result.json', dict(status='PASS_LIMITED_REAL_ROS_REPLAY', phases=report,
             physical_input=False, physical_stop=False, production_mapping_enabled=False))
        return 0
    except BaseException as exc:
        save(root / 'result.json', dict(status='FAILED_FROZEN_NO_REPLAY', error=repr(exc)))
        raise


if __name__ == '__main__':
    raise SystemExit(main())
