"""恢复保护：旧缓存/无线down/超时回调竞态及真实节点方法组合，无设备。"""
from dataclasses import replace
import importlib
import json
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from p0_manual_control.core import JoyMapping, ManualRecoveryGuard

MAPPING = JoyMapping(True, 1, 3, 5, -.2, -.8, .1)
HELD = ([0., 0., 0., .99], [0, 0, 0, 0, 0, 1])
NEUTRAL = ([0., 0., 0., 0.], [0] * 6)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.guard = ManualRecoveryGuard()
        self.now = 1.

    def observe(self, sample=HELD, alive=True, mapping=MAPPING, advance=.05):
        self.now += advance
        return self.guard.observe(*sample, mapping, self.now, .25, alive)

    def lose(self):
        self.assertTrue(self.observe().active)
        self.assertFalse(self.observe(NEUTRAL, alive=False).active)

    def test_startup_down_does_not_reclassify_initial_input_as_recovery(self):
        self.assertFalse(self.observe(NEUTRAL, alive=False).active)
        self.assertTrue(self.observe().active)

    def test_cached_held_recovery_stays_zero_until_released_neutral(self):
        self.lose()
        for _ in range(20):
            result = self.observe()
            self.assertFalse(result.active)
            self.assertEqual((result.linear_x_mps, result.angular_z_radps), (0., 0.))
        self.assertFalse(self.observe((HELD[0], NEUTRAL[1])).active)
        self.assertFalse(self.observe((NEUTRAL[0], HELD[1])).active)
        self.assertEqual(self.observe(NEUTRAL).reason, 'recovery_neutral_seen')
        self.assertTrue(self.observe().active)

    def test_down_neutral_does_not_unlock(self):
        self.lose()
        for _ in range(10):
            self.assertFalse(self.observe(NEUTRAL, alive=False).active)
        self.assertEqual(self.observe().reason, 'recovery_neutral_required')

    def test_timeout_callback_before_timer_still_locks(self):
        self.assertTrue(self.observe().active)
        self.assertEqual(self.observe(advance=.30).reason, 'recovery_neutral_required')
        self.assertFalse(self.observe(NEUTRAL).active)
        self.assertTrue(self.observe().active)

    def test_timer_timeout_locks_repeated_loss(self):
        self.assertTrue(self.observe().active)
        for _ in range(2):
            self.guard.require_neutral()
            self.assertFalse(self.observe().active)
            self.assertFalse(self.observe(NEUTRAL).active)
            self.assertTrue(self.observe().active)

    def test_missing_nonfinite_or_unconfirmed_neutral_never_unlocks(self):
        self.lose()
        samples = [([], []), ([0., 0., 0., float('nan')], NEUTRAL[1]),
                   ([0., float('inf'), 0., 0.], NEUTRAL[1])]
        for sample in samples:
            self.assertFalse(self.observe(sample).active)
            self.assertEqual(self.observe().reason, 'recovery_neutral_required')
        for mapping in [replace(MAPPING, mapping_confirmed=False),
                        replace(MAPPING, angular_axis=-1), replace(MAPPING, deadman_button=10)]:
            self.assertFalse(self.observe(NEUTRAL, mapping=mapping).active)
            self.assertEqual(self.observe().reason, 'recovery_neutral_required')

    def test_healthy_continuous_hold_and_ordinary_rb_release_unchanged(self):
        for _ in range(100):
            self.assertTrue(self.observe().active)
        self.assertFalse(self.observe((HELD[0], NEUTRAL[1])).active)
        self.assertTrue(self.observe().active)


class ActualNodeTests(unittest.TestCase):
    def test_real_input_methods_old_cache_blocked_then_fresh_raw_control(self):
        repo = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(repo / 'tools/nano_bench'))
        from test_ros_replay_bench import FakeROS
        fake = FakeROS(); count = 100; latest = {}
        with patch.dict(sys.modules, fake.modules), patch.object(fake.modules['rclpy.node'].Node, 'get_logger', return_value=SimpleNamespace(info=lambda *a: None, warning=lambda *a: None)):
            for name in ('p0_manual_control.linux_joy_node', 'p0_manual_control.node'):
                sys.modules.pop(name, None)
            linux = importlib.import_module('p0_manual_control.linux_joy_node')
            manual = importlib.import_module('p0_manual_control.node')
            reader = linux.LinuxJoyNode(); adapter = manual.ManualControlNode()
            adapter.params.update(mapping_confirmed=True, linear_axis=1, angular_axis=3, deadman_button=5, linear_scale=-.2, angular_scale=-.8)
            observer = fake.modules['rclpy'].create_node('test_observer')
            observer.create_subscription(fake.Message, '/p0/manual/cmd_vel', lambda m: latest.update(active=m.active, angular=m.angular_z_radps), 10)
            reader._fd = 999998; reader._device = '/TEMPORARY_TEST_ONLY'
            reader._heartbeat_path = SimpleNamespace(read_text=lambda **kw: str(count))
            reader._axes = list(HELD[0]); reader._buttons = list(HELD[1])
            def publish(now, counter):
                nonlocal count
                count = counter
                with patch.object(linux.time, 'monotonic', return_value=now):
                    reader._publish_tick(); adapter._tick()
            publish(1., 100); publish(1.05, 101)
            self.assertTrue(latest['active'])
            publish(1.50, 101); self.assertFalse(latest['active'])
            publish(1.55, 102); self.assertTrue(reader._link_alive)
            self.assertEqual(reader._buttons[5], 1)  # 原输入节点确实保留旧缓存。
            self.assertFalse(latest['active']); self.assertEqual(latest['angular'], 0.)
            for now, angular, rb, expected in [(1.60, 0, 0, False), (1.65, 32767, 1, True)]:
                data = b''.join(struct.pack('=IhBB', 1, v, k, n) for v, k, n in [(angular, 2, 3), (rb, 1, 5)])
                with patch.object(linux.os, 'read', side_effect=[data, BlockingIOError()]):
                    reader._read_tick()
                publish(now, count + 1)
                self.assertEqual(latest['active'], expected)
            reader._fd = None
            for node in reversed(fake.nodes[:]):
                node.destroy_node()

    def test_real_adapter_timer_timeout_and_callback_race(self):
        repo = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(repo / 'tools/nano_bench'))
        from test_ros_replay_bench import FakeROS
        for timer_first in (False, True):
            fake = FakeROS(); latest = {}
            with patch.dict(sys.modules, fake.modules):
                sys.modules.pop('p0_manual_control.node', None)
                module = importlib.import_module('p0_manual_control.node')
                node = module.ManualControlNode()
                node.params.update(mapping_confirmed=True, linear_axis=1, angular_axis=3, deadman_button=5)
                observer = fake.modules['rclpy'].create_node('observer')
                observer.create_subscription(fake.Message, '/p0/manual/cmd_vel', lambda m: latest.update(active=m.active), 10)
                def joy(sample, when):
                    message = fake.Message(); message.header.frame_id = '/fixture/js0'
                    message.axes, message.buttons = sample
                    with patch.object(module.time, 'monotonic', return_value=when):
                        node._on_joy(message); node._tick()
                joy(HELD, 1.)
                if timer_first:
                    with patch.object(module.time, 'monotonic', return_value=1.30): node._tick()
                joy(HELD, 1.35); self.assertFalse(latest['active'])
                joy(NEUTRAL, 1.40); joy(HELD, 1.45); self.assertTrue(latest['active'])
                for n in reversed(fake.nodes[:]): n.destroy_node()


if __name__ == '__main__':
    unittest.main()
