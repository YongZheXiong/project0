"""真实模式core到最终指令仲裁的代表性序列及关键失效反例。"""
import unittest
from p0_safety_manager.core import CommandArbiter, MotionInput, ModePermission


def arbiter():
    a=CommandArbiter(manual_timeout_sec=.25,autonomy_timeout_sec=.25,
        manual_release_hold_sec=.5,autonomy_enabled=True,require_system_mode=True)
    a.update_base_state(comm_ok=True,motion_ready=True)
    return a


def permission(at=1.,mode='MANUAL',generation=1,epoch='SYNTHETIC'):
    return ModePermission(mode,mode=='MANUAL',mode=='FAULT',epoch,generation,at)


def neutral(a,at):a.update_manual(MotionInput(0.,0.,False,at))
def active(a,at):a.update_manual(MotionInput(.1,.2,True,at))


class ModeArbitrationTests(unittest.TestCase):
    def test_no_mode_standby_and_initially_held_input_stop_then_real_neutral_allows_new_input(self):
        a=arbiter();active(a,1.)
        self.assertFalse(a.decide(1.).active)
        a.update_system_mode(permission(mode='STANDBY',generation=0));active(a,1.)
        self.assertFalse(a.decide(1.).active)
        a.update_system_mode(permission());active(a,1.01)
        self.assertFalse(a.decide(1.01).active)
        neutral(a,1.02);self.assertFalse(a.decide(1.02).active)
        active(a,1.03);self.assertTrue(a.decide(1.03).active)
        a.update_autonomy(MotionInput(.2,0.,True,1.04));neutral(a,1.04)
        self.assertFalse(a.decide(1.04).active)  # MANUAL许可不通向自动源。

    def test_fault_recovery_and_process_epoch_change_discard_old_intent(self):
        a=arbiter();a.update_system_mode(permission());neutral(a,1.);active(a,1.01)
        self.assertTrue(a.decide(1.02).active)
        a.update_system_mode(permission(1.03,'FAULT',2));self.assertIsNone(a.manual)
        a.update_system_mode(permission(1.04,'MANUAL',4));active(a,1.05)
        self.assertFalse(a.decide(1.05).active)
        neutral(a,1.06);active(a,1.07);self.assertTrue(a.decide(1.07).active)
        a.update_system_mode(permission(1.08,epoch='SYNTHETIC-NEW'));active(a,1.09)
        self.assertFalse(a.decide(1.09).active)

    def test_stale_or_out_of_order_mode_does_not_refresh_permission(self):
        a=arbiter();a.update_system_mode(permission(generation=4));neutral(a,1.);active(a,1.01)
        a.update_system_mode(permission(1.2,generation=3))
        self.assertEqual(a.system_mode.received_at,1.)
        self.assertFalse(a.decide(1.26).active);self.assertIsNone(a.manual)
        a.update_system_mode(permission(1.27,generation=4));active(a,1.28)
        self.assertFalse(a.decide(1.28).active)

    def test_base_loss_or_software_lock_clear_requires_new_neutral(self):
        a=arbiter();a.update_system_mode(permission());neutral(a,1.);active(a,1.01)
        a.update_base_state(comm_ok=False,motion_ready=False)
        a.update_base_state(comm_ok=True,motion_ready=True);active(a,1.02)
        self.assertFalse(a.decide(1.02).active)
        neutral(a,1.03);active(a,1.04);self.assertTrue(a.decide(1.04).active)
        a.latch_motion_lock('test');a.clear_motion_lock();active(a,1.05)
        self.assertFalse(a.decide(1.05).active)

    def test_invalid_permission_and_nonfinite_active_command_cannot_pass(self):
        a=arbiter();bad=ModePermission('STANDBY',True,False,'SYNTHETIC',1,1.)
        a.update_system_mode(bad);neutral(a,1.);active(a,1.01);self.assertFalse(a.decide(1.01).active)
        a.update_system_mode(permission());neutral(a,1.)
        a.update_manual(MotionInput(float('nan'),0.,True,1.01))
        self.assertFalse(a.decide(1.02).active);self.assertTrue(a.software_motion_lock_latched)


if __name__=='__main__':unittest.main()
