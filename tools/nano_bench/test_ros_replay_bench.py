"""无设备组合检查：实际入口/真实节点方法，ROS/DDS/时钟为明确替身。"""
import copy
import importlib
import io
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

import ros_replay_bench as bench


def fixture():
    def row(linear=0.02, angular=0.02, deadman=0):
        return dict(axes=[0., linear, 0., angular], buttons=[0, 0, 0, 0, 0, deadman])
    return dict(inputs=dict(neutral=row(), forward=row(-.98, deadman=1),
                backward=row(.99, deadman=1), left=row(angular=-.99, deadman=1),
                right=row(angular=.98, deadman=1), released=row(-.98)))


class FakeROS:
    """实现真实run_ros使用的ROS接口；不打开设备、不生成实体结果。"""
    def __init__(self):
        self.now = 1.0
        self.nodes = []
        self.subscriptions = {}
        self.services = {}
        self.timers = []
        self.ok = True
        self.remaps = {}
        self.namespace = ''
        self.drop = None
        self.failed_service = False
        self.foreign = False
        self.mutate = None
        owner = self
        class Message:
            def __init__(self):
                self.header = SimpleNamespace(stamp=None, frame_id='')
        self.Message = Message
        class Publisher:
            def __init__(self, topic): self.topic = owner.remaps.get(topic, topic)
            def publish(self, message):
                if owner.drop and self.topic.endswith(owner.drop): return
                if owner.mutate: owner.mutate(self.topic, message)
                for node, callback in list(owner.subscriptions.get(self.topic, [])):
                    if node in owner.nodes: callback(message)
            def get_subscription_count(self): return len(owner.subscriptions.get(self.topic, []))
        class Timer(list):
            @property
            def callback(self):return self[3]
            def cancel(self):
                if self in owner.timers:owner.timers.remove(self)

        class Node:
            def __init__(self, name):
                self.name = name; self.params = {}; owner.nodes.append(self)
            def declare_parameter(self, name, default): self.params[name] = default
            def get_parameter(self, name): return SimpleNamespace(value=self.params[name])
            def set_parameters(self, params):
                for p in params: self.params[p.name] = p.value
                return [SimpleNamespace(successful=True) for _ in params]
            def create_publisher(self, kind, topic, depth): return Publisher(topic)
            def create_subscription(self, kind, topic, callback, depth):
                owner.subscriptions.setdefault(owner.remaps.get(topic, topic), []).append((self, callback))
            def create_timer(self, period, callback):
                timer=Timer([self, period, owner.now + period, callback]);owner.timers.append(timer);return timer
            @property
            def timers(self):return (timer for timer in owner.timers if timer[0] is self)
            def get_clock(self): return SimpleNamespace(now=lambda: SimpleNamespace(to_msg=lambda: None))
            def get_logger(self): return SimpleNamespace(info=lambda *a: None)
            def get_node_names_and_namespaces(self):
                return [(n.name, owner.namespace) for n in owner.nodes] + ([('foreign', '/')] if owner.foreign else [])
            def get_topic_names_and_types(self): return [(t, []) for t in owner.subscriptions]
            def create_service(self, kind, topic, callback): owner.services[owner.remaps.get(topic, topic)] = callback
            def create_client(self, kind, topic):
                topic = owner.remaps.get(topic, topic)
                def call(request):
                    response = owner.services[topic](request, SimpleNamespace())
                    if owner.failed_service: response.success = False
                    return SimpleNamespace(done=lambda: True, result=lambda: response)
                return SimpleNamespace(service_is_ready=lambda: topic in owner.services, call_async=call)
            def destroy_node(self):
                owner.nodes.remove(self)
                owner.timers[:] = [t for t in owner.timers if t[0] is not self]
                for topic in owner.subscriptions:
                    owner.subscriptions[topic][:] = [(n,c) for n,c in owner.subscriptions[topic] if n is not self]
        class Executor:
            def add_node(self, node): pass
            def remove_node(self, node): pass
            def shutdown(self): pass
            def spin_once(self, timeout_sec):
                owner.now += timeout_sec
                for timer in list(owner.timers):
                    if timer[2] <= owner.now:
                        timer[2] = owner.now + timer[1]; timer[3]()
        class Parameter:
            def __init__(self, name, value): self.name = name; self.value = value
        def init(args):
            for i, item in enumerate(args):
                if item == '-r':
                    key, value = args[i+1].split(':=')
                    if key == '__ns': owner.namespace = value
                    else: owner.remaps[key] = value
        def module(name, **values):
            result = ModuleType(name); result.__dict__.update(values); return result
        self.modules = {
            'rclpy': module('rclpy', init=init, create_node=Node, ok=lambda: owner.ok,
                            shutdown=lambda: setattr(owner, 'ok', False)),
            'rclpy.node': module('rclpy.node', Node=Node),
            'rclpy.executors': module('rclpy.executors', SingleThreadedExecutor=Executor),
            'rclpy.parameter': module('rclpy.parameter', Parameter=Parameter),
            'sensor_msgs': module('sensor_msgs'),
            'sensor_msgs.msg': module('sensor_msgs.msg', Joy=Message),
            'p0_interfaces': module('p0_interfaces'),
            'p0_interfaces.msg': module('p0_interfaces.msg', ChassisCmd=Message, ChassisStatus=Message),
            'p0_interfaces.srv': module('p0_interfaces.srv', StopMotion=SimpleNamespace(Request=Message),
                                       ClearMotionLock=SimpleNamespace(Request=Message)),
        }

    def run(self, root, data):
        repo = Path(__file__).resolve().parents[2]
        with patch.dict(sys.modules, self.modules), patch.object(bench.time, 'monotonic', lambda: self.now), \
             patch.object(sys, 'path', [str(repo/'src/p0_manual_control'), str(repo/'src/p0_safety_manager')] + sys.path), \
             patch('sys.stdout', new=io.StringIO()):
            for name in ('p0_manual_control.node', 'p0_safety_manager.node'): sys.modules.pop(name, None)
            return bench.run_ros(root, data)


class ReplayTests(unittest.TestCase):
    def test_full_actual_entry_and_node_methods(self):
        with tempfile.TemporaryDirectory() as temp:
            ros = FakeROS(); reports = ros.run(Path(temp), fixture())
            self.assertEqual(len(reports), 18)
            self.assertFalse(ros.nodes)
            rows = [json.loads(x) for x in (Path(temp)/'outputs.jsonl').read_text().splitlines()]
            self.assertGreater(len(rows), 700)
            self.assertTrue((Path(temp)/'ros_cleanup.json').exists())

    def test_wrong_output_fails_and_cleans_up(self):
        def corrupt(topic, message):
            if topic.endswith('/p0/base/cmd_vel') and message.active: message.linear_x_mps = 9.0
        with tempfile.TemporaryDirectory() as temp:
            ros=FakeROS(); ros.mutate=corrupt
            with self.assertRaisesRegex(ValueError, 'UNEXPECTED_OUTPUT'): ros.run(Path(temp),fixture())
            self.assertFalse(ros.nodes)

    def test_missing_output_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            ros=FakeROS(); ros.drop='/p0/base/cmd_vel'
            with self.assertRaisesRegex(ValueError, 'MISSING_OUTPUT'): ros.run(Path(temp),fixture())
            self.assertFalse(ros.nodes)

    def test_foreign_graph_rejected_before_control_nodes(self):
        with tempfile.TemporaryDirectory() as temp:
            ros=FakeROS(); ros.foreign=True
            with self.assertRaisesRegex(ValueError, 'DDS_DOMAIN_ALREADY_OCCUPIED'): ros.run(Path(temp),fixture())
            self.assertFalse(ros.nodes)

    def test_service_failure_stops_and_preserves_rows(self):
        with tempfile.TemporaryDirectory() as temp:
            ros=FakeROS(); ros.failed_service=True
            with self.assertRaisesRegex(ValueError, 'FIXTURE_SERVICE_FAILED'): ros.run(Path(temp),fixture())
            self.assertFalse(ros.nodes)
            self.assertGreater((Path(temp)/'outputs.jsonl').stat().st_size, 1000)

    def test_assessor_rejects_one_bad_frame_nan_and_gap(self):
        phase=bench.Phase('neutral','neutral',bench.ZERO)
        rows=[dict(stream=stream,elapsed=0.60+i*.05,active=False,linear=0.,angular=0.,source='safety')
              for stream in ('manual','base') for i in range(12)]
        bench.assess(phase,rows)
        for value in (0.02, float('nan')):
            bad=copy.deepcopy(rows);bad[-1]['linear']=value
            with self.assertRaisesRegex(ValueError,'UNEXPECTED_OUTPUT'):bench.assess(phase,bad)
        bad=[r for r in rows if r['stream']=='manual' or r['elapsed']<.7 or r['elapsed']>1.0]
        with self.assertRaisesRegex(ValueError,'OUTPUT_STALL'):bench.assess(phase,bad)

    def test_final_validator_positive_missing_fields_and_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'frozen').write_text('fixed')
            plan=dict(id=bench.PLAN_ID,scope=bench.SCOPE,files={'frozen':bench.sha(root/'frozen')})
            bench.save(root/'plan.json',plan)
            auth=dict(approved=True,plan_id=bench.PLAN_ID,plan_sha256=bench.sha(root/'plan.json'),
                      scope=bench.SCOPE,source_text='synthetic approval only in temp fixture',source_thread='test',approved_at='test')
            path=root/'authorization.json';bench.save(path,auth);bench.verify_package(root)
            for field in auth:
                bad=dict(auth);del bad[field];path.write_text(json.dumps(bad))
                with self.assertRaisesRegex(ValueError,'AUTHORIZATION'):bench.verify_package(root)
            path.write_text(json.dumps(dict(auth,approved=False)))
            with self.assertRaisesRegex(ValueError,'AUTHORIZATION'):bench.verify_package(root)
            path.write_text(json.dumps(auth));(root/'frozen').write_text('changed')
            with self.assertRaisesRegex(ValueError,'SOURCE_DRIFT'):bench.verify_package(root)
            (root/'frozen').write_text('fixed');bench.save(root/'started.json',{})
            with self.assertRaisesRegex(ValueError,'CONSUMED'):bench.verify_package(root)

    def test_authorization_rejection_precedes_ros_import_and_preflight(self):
        with patch.object(bench,'verify_package',side_effect=ValueError('not approved')), \
             patch.object(bench,'preflight') as check, patch.object(bench,'run_ros') as run, \
             patch.object(sys,'argv',['bench','--package','/tmp/test-only']):
            with self.assertRaisesRegex(ValueError,'not approved'):bench.main()
            check.assert_not_called();run.assert_not_called()

    def test_actual_preflight_board_usb_process_and_dds_rejections(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            def put(name, value):
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(value)
            put('proc/device-tree/serial-number',b'fixture-only')
            put('proc/sys/kernel/random/boot_id',b'fixture-boot')
            plan=dict(serial_sha256=hashlib.sha256(b'fixture-only').hexdigest(),boot='fixture-boot')
            with patch.object(bench,'Path',side_effect=lambda p: root/str(p).lstrip('/')), \
                 patch.dict(bench.os.environ,ROS_DOMAIN_ID='188',ROS_LOCALHOST_ONLY='1'):
                bench.preflight(plan)
                put('proc/999998/cmdline',b'sh\0-c\0python -c "plan contains p0_manual_control.node"\0')
                bench.preflight(plan)
                with self.assertRaisesRegex(ValueError,'BOARD_OR_BOOT'):bench.preflight(dict(plan,boot='wrong'))
                put('sys/bus/usb/devices/1-2/idVendor',b'1a86');put('sys/bus/usb/devices/1-2/idProduct',b'55d4')
                with self.assertRaisesRegex(ValueError,'H60_USB_PRESENT'):bench.preflight(plan)
                (root/'sys/bus/usb/devices/1-2/idProduct').write_text('0000')
                put('proc/999999/cmdline',b'python\0p0_base_bridge\0')
                with self.assertRaisesRegex(ValueError,'OTHER_CONTROL_PROCESS'):bench.preflight(plan)
                (root/'proc/999999/cmdline').unlink()
                with patch.dict(bench.os.environ,ROS_DOMAIN_ID='0'):
                    with self.assertRaisesRegex(ValueError,'DDS_ISOLATION'):bench.preflight(plan)


if __name__ == '__main__': unittest.main()
