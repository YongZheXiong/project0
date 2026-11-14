"""模式实际行为与恢复契约，不访问ROS或设备。"""
import unittest
from p0_system_manager.core import BaseState, ManualState, SystemModeManager


class ModeTests(unittest.TestCase):
    def manager(self, now=1.):
        m=SystemModeManager(epoch='SYNTHETIC')
        m.update_base(BaseState(True,True,False,now))
        m.update_manual(ManualState(False,0.,0.,now))
        return m

    def test_startup_and_explicit_manual_require_ready_neutral_input(self):
        m=SystemModeManager(epoch='SYNTHETIC')
        self.assertEqual(m.evaluate(1.).mode,'STANDBY')
        self.assertFalse(m.request_mode('MANUAL',1.)[0])
        m=self.manager();self.assertTrue(m.request_mode('MANUAL',1.)[0])
        state=m.evaluate(1.01);self.assertTrue(state.motion_allowed);self.assertEqual(state.generation,1)
        self.assertFalse(m.request_mode('AUTONOMOUS',1.01)[0])
        self.assertEqual(m.mode,'MANUAL')

    def test_held_nonzero_nonfinite_or_future_input_cannot_grant_manual(self):
        for command in (ManualState(True,0.,0.,1.),ManualState(False,.1,0.,1.),
                ManualState(False,float('nan'),0.,1.),ManualState(False,0.,0.,2.)):
            with self.subTest(command=command):
                m=self.manager();m.update_manual(command)
                self.assertFalse(m.request_mode('MANUAL',1.)[0])
                self.assertFalse(m.evaluate(1.).motion_allowed)

    def test_communication_loss_latches_and_recovery_never_resumes_automatically(self):
        m=self.manager();m.request_mode('MANUAL',1.)
        m.update_manual(ManualState(True,.1,0.,1.2))
        self.assertEqual(m.evaluate(1.36).mode,'FAULT')
        m.update_base(BaseState(True,True,False,2.))
        m.update_manual(ManualState(False,0.,0.,2.))
        self.assertFalse(m.evaluate(2.).motion_allowed)
        self.assertFalse(m.request_mode('MANUAL',2.)[0])
        self.assertTrue(m.request_mode('STANDBY',2.)[0])
        self.assertFalse(m.evaluate(2.).motion_allowed)
        self.assertTrue(m.request_mode('MANUAL',2.)[0])
        self.assertTrue(m.evaluate(2.).motion_allowed)
        self.assertEqual(m.generation,4)

    def test_hardware_fault_cannot_be_cleared_by_mode_request(self):
        m=self.manager();m.update_base(BaseState(True,False,True,1.))
        self.assertEqual(m.evaluate(1.).mode,'FAULT')
        self.assertFalse(m.request_mode('STANDBY',1.)[0])
        m.update_base(BaseState(True,False,False,1.1))
        self.assertTrue(m.request_mode('STANDBY',1.1)[0])
        self.assertFalse(m.request_mode('MANUAL',1.1)[0])

    def test_missing_manual_freshness_and_explicit_standby_remove_permission(self):
        m=self.manager();m.request_mode('MANUAL',1.)
        m.update_base(BaseState(True,True,False,1.2))
        self.assertTrue(m.evaluate(1.25).motion_allowed)
        self.assertEqual(m.evaluate(1.250001).mode,'FAULT')
        m=self.manager();m.request_mode('MANUAL',1.)
        m.update_manual(ManualState(True,.1,0.,1.1))
        self.assertTrue(m.request_mode('STANDBY',1.1)[0])
        self.assertFalse(m.evaluate(1.1).motion_allowed)

    def test_invalid_timeout_or_empty_epoch_never_constructs(self):
        for options in (dict(epoch=''),dict(epoch='x',base_timeout_sec=0),
                dict(epoch='x',manual_timeout_sec=float('nan'))):
            with self.subTest(options=options),self.assertRaises(ValueError):SystemModeManager(**options)


if __name__=='__main__':unittest.main()
