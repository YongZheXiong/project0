"""实际两个ROS节点的消息/服务/许可/故障链；ROS总线明确使用隔离替身。"""
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]


def message_type(name,definition):
    fields=[]
    for line in definition.splitlines():
        line=line.split('#',1)[0].strip()
        if line:
            kind,key=line.split();fields.append((kind,key))
    def init(self,**values):
        for kind,key in fields:
            value=(SimpleNamespace(stamp=None,frame_id='') if kind=='std_msgs/Header' else
                   '' if kind=='string' else False if kind=='bool' else 0. if kind.startswith('float') else 0)
            setattr(self,key,value)
        for key,value in values.items():setattr(self,key,value)
    return type(name,(),{'__slots__':tuple(key for _,key in fields),'__init__':init})


class NodeContractTests(unittest.TestCase):
    def run_nodes(self,scenario):
        now=[1.];topics={};services={};publications=[];parameters={}
        msg_module=ModuleType('p0_interfaces.msg');srv_module=ModuleType('p0_interfaces.srv')
        for name in ('ChassisCmd','ChassisStatus','SystemStatus'):
            setattr(msg_module,name,message_type(name,(ROOT/'src/p0_interfaces/msg'/(name+'.msg')).read_text()))
        for name in ('StopMotion','ClearMotionLock','SetSystemMode'):
            request,response=(ROOT/'src/p0_interfaces/srv'/(name+'.srv')).read_text().split('---')
            setattr(srv_module,name,SimpleNamespace(Request=message_type(name+'Request',request),
                Response=message_type(name+'Response',response)))
        def publish(topic,message):
            publications.append((topic,message))
            for callback in list(topics.get(topic,[])):callback(message)
        class Client:
            def __init__(self,kind,topic):self.kind,self.topic=kind,topic
            def service_is_ready(self):return self.topic in services
            def call_async(self,request):
                if parameters.get(('SYNTHETIC','client_fail')):
                    raise RuntimeError('SYNTHETIC_RPC_FAILURE')
                response=services[self.topic](request,self.kind.Response())
                return SimpleNamespace(result=lambda:response,add_done_callback=lambda fn:fn(SimpleNamespace(result=lambda:response)))
        class Node:
            def __init__(self,name):self.name=name;self.params={}
            def declare_parameter(self,key,value):self.params[key]=parameters.get((self.name,key),value)
            def get_parameter(self,key):return SimpleNamespace(value=self.params[key])
            def create_publisher(self,kind,topic,depth):
                def send(message):
                    assert isinstance(message,kind)
                    publish(topic,message)
                return SimpleNamespace(publish=send)
            def create_subscription(self,kind,topic,callback,depth):topics.setdefault(topic,[]).append(callback)
            def create_service(self,kind,topic,callback):services[topic]=callback
            def create_client(self,kind,topic):return Client(kind,topic)
            def create_timer(self,period,callback):self.assert_period=period
            def get_clock(self):return SimpleNamespace(now=lambda:SimpleNamespace(to_msg=lambda:None))
            def get_logger(self):return SimpleNamespace(info=lambda *a:None,warning=lambda *a:None)
            def destroy_node(self):pass
        rclpy=ModuleType('rclpy');node_module=ModuleType('rclpy.node');node_module.Node=Node
        modules={'rclpy':rclpy,'rclpy.node':node_module,'p0_interfaces':ModuleType('p0_interfaces'),
            'p0_interfaces.msg':msg_module,'p0_interfaces.srv':srv_module}
        node_names=('p0_system_manager.node','p0_safety_manager.node')
        previous={name:sys.modules.pop(name,None) for name in node_names}
        missing=object()
        parent_nodes={name.rsplit('.',1)[0]:getattr(sys.modules.get(name.rsplit('.',1)[0]),'node',missing)
                      for name in node_names}
        try:
            with patch.dict(sys.modules,modules):
                manager=importlib.import_module(node_names[0]);safety=importlib.import_module(node_names[1])
                with patch.object(manager.time,'monotonic',lambda:now[0]):
                    scenario(SimpleNamespace(now=now,publish=publish,services=services,msg=msg_module,
                        srv=srv_module,manager=manager,safety=safety,publications=publications,parameters=parameters))
        finally:
            for name in node_names:
                sys.modules.pop(name,None)
                if previous[name] is not None:sys.modules[name]=previous[name]
            for package,value in parent_nodes.items():
                parent=sys.modules.get(package)
                if parent is not None:
                    if value is missing:
                        if hasattr(parent,'node'):delattr(parent,'node')
                    else:setattr(parent,'node',value)

    def test_actual_nodes_route_explicit_permission_stop_fault_clear_and_no_auto_resume(self):
        def scenario(bus):
            m=bus.manager.SystemManagerNode();a=bus.safety.SafetyManagerNode()
            def base():bus.publish('/p0/base/status',bus.msg.ChassisStatus(comm_ok=True,motion_ready=True,fault_latched=False))
            def manual(on):bus.publish('/p0/manual/cmd_vel',bus.msg.ChassisCmd(active=on,linear_x_mps=.1 if on else 0.,angular_z_radps=0.))
            def mode(target):return bus.services['/p0/system/set_mode'](bus.srv.SetSystemMode.Request(target_mode=target),bus.srv.SetSystemMode.Response())
            def output():
                a._tick();return [msg for topic,msg in bus.publications if topic=='/p0/base/cmd_vel'][-1]
            m._publish();base();manual(False)
            self.assertFalse(output().active)
            response=mode('MANUAL');self.assertTrue(response.success);self.assertEqual(response.current_mode,'MANUAL')
            manual(True);self.assertFalse(output().active)
            manual(False);self.assertFalse(output().active)
            manual(True);self.assertTrue(output().active)
            stopped=a._on_stop_motion(bus.srv.StopMotion.Request(reason='SYNTHETIC'),bus.srv.StopMotion.Response())
            self.assertTrue(stopped.success);self.assertFalse(output().active);self.assertEqual(m._manager.mode,'FAULT')
            self.assertTrue(a._on_clear_motion_lock(bus.srv.ClearMotionLock.Request(),bus.srv.ClearMotionLock.Response()).success)
            manual(False);self.assertTrue(mode('STANDBY').success);self.assertFalse(output().active)
            self.assertTrue(mode('MANUAL').success);manual(True);self.assertFalse(output().active)
            manual(False);manual(True);self.assertTrue(output().active)
            bus.now[0]+=.4;m._publish();self.assertFalse(output().active);self.assertEqual(m._manager.mode,'FAULT')
        self.run_nodes(scenario)

    def test_safety_stops_without_authority_and_node_cannot_disable_mode_gate(self):
        def scenario(bus):
            bus.parameters[('p0_safety_manager','require_system_mode')]=False
            with self.assertRaises(ValueError):bus.safety.SafetyManagerNode()
            bus.parameters.clear();a=bus.safety.SafetyManagerNode()
            bus.publish('/p0/base/status',bus.msg.ChassisStatus(comm_ok=True,motion_ready=True))
            bus.publish('/p0/manual/cmd_vel',bus.msg.ChassisCmd(active=True,linear_x_mps=.1))
            a._tick();self.assertFalse(bus.publications[-1][1].active)
            a._on_stop_motion(bus.srv.StopMotion.Request(reason='SYNTHETIC'),bus.srv.StopMotion.Response())
            self.assertTrue(a._arbiter.software_motion_lock_latched)
            self.assertTrue(a._fault_request_pending)
            self.assertFalse(a._on_clear_motion_lock(bus.srv.ClearMotionLock.Request(),bus.srv.ClearMotionLock.Response()).success)
            m=bus.manager.SystemManagerNode();m._publish();a._tick()
            self.assertEqual(m._manager.mode,'FAULT');self.assertFalse(a._fault_request_pending)
            self.assertFalse(bus.publications[-1][1].active)
        self.run_nodes(scenario)

    def test_mode_client_exception_cannot_prevent_local_stop_or_zero_publish(self):
        def scenario(bus):
            m=bus.manager.SystemManagerNode();a=bus.safety.SafetyManagerNode()
            bus.publish('/p0/base/status',bus.msg.ChassisStatus(comm_ok=True,motion_ready=True))
            bus.publish('/p0/manual/cmd_vel',bus.msg.ChassisCmd())
            response=bus.services['/p0/system/set_mode'](bus.srv.SetSystemMode.Request(target_mode='MANUAL'),bus.srv.SetSystemMode.Response())
            self.assertTrue(response.success)
            bus.publish('/p0/manual/cmd_vel',bus.msg.ChassisCmd())
            bus.publish('/p0/manual/cmd_vel',bus.msg.ChassisCmd(active=True,linear_x_mps=.1))
            a._tick();self.assertTrue(bus.publications[-1][1].active)
            bus.parameters[('SYNTHETIC','client_fail')]=True
            response=a._on_stop_motion(bus.srv.StopMotion.Request(reason='SYNTHETIC'),bus.srv.StopMotion.Response())
            self.assertTrue(response.success);a._tick()
            self.assertFalse(bus.publications[-1][1].active)
            self.assertTrue(a._arbiter.software_motion_lock_latched)
            self.assertFalse(a._on_clear_motion_lock(bus.srv.ClearMotionLock.Request(),bus.srv.ClearMotionLock.Response()).success)
        self.run_nodes(scenario)

    def test_actual_main_closes_context_after_spin_or_destroy_interrupt_but_preserves_real_error(self):
        def scenario(bus):
            for spin_error,destroy_error in ((None,None),(KeyboardInterrupt,None),
                    (None,KeyboardInterrupt),(KeyboardInterrupt,KeyboardInterrupt),(None,RuntimeError)):
                calls=[]
                def spin(node):
                    calls.append('spin')
                    if spin_error:raise spin_error('EXPLICIT_OFFLINE_SPIN')
                def destroy():
                    calls.append('destroy')
                    if destroy_error:raise destroy_error('EXPLICIT_OFFLINE_DESTROY')
                node=SimpleNamespace(destroy_node=destroy)
                with self.subTest(spin=spin_error,destroy=destroy_error),\
                        patch.object(bus.manager,'SystemManagerNode',return_value=node),\
                        patch.object(bus.manager.rclpy,'init',lambda **kw:calls.append('init'),create=True),\
                        patch.object(bus.manager.rclpy,'spin',spin,create=True),\
                        patch.object(bus.manager.rclpy,'ok',lambda:True,create=True),\
                        patch.object(bus.manager.rclpy,'shutdown',lambda:calls.append('shutdown'),create=True):
                    if destroy_error is RuntimeError:
                        with self.assertRaisesRegex(RuntimeError,'EXPLICIT_OFFLINE_DESTROY'):bus.manager.main()
                    else:bus.manager.main()
                    self.assertEqual(calls,['init','spin','destroy','shutdown'])
        self.run_nodes(scenario)


if __name__=='__main__':unittest.main()
