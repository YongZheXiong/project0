"""实际launch生成入口的节点/参数契约；launch与ROS均隔离替身。"""
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import patch


class LaunchTests(unittest.TestCase):
    def test_both_launches_include_authority_and_keep_original_motion_locks(self):
        root=Path(__file__).resolve().parents[1]
        class Action:
            def __init__(self,*args,**kwargs):self.args,self.kwargs=args,kwargs
        modules={}
        for name in ('ament_index_python','ament_index_python.packages','launch','launch_ros',
                     'launch_ros.actions','launch.actions','launch.substitutions'):
            modules[name]=ModuleType(name)
        modules['ament_index_python.packages'].get_package_share_directory=lambda _:str(root)
        modules['launch'].LaunchDescription=lambda actions:actions
        modules['launch_ros.actions'].Node=Action
        modules['launch.actions'].DeclareLaunchArgument=Action
        modules['launch.substitutions'].LaunchConfiguration=Action
        with patch.dict(sys.modules,modules):
            for name in ('base_control_no_motion','orin_return_no_motion'):
                spec=importlib.util.spec_from_file_location(name,root/'launch'/(name+'.launch.py'))
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                actions=module.generate_launch_description();nodes=[a.kwargs for a in actions if 'package' in a.kwargs]
                self.assertEqual(sum(n['package']=='p0_system_manager' for n in nodes),1)
                self.assertEqual(len(nodes),5)
                for n in nodes:
                    self.assertEqual(n['parameters'][0],str(root/'config/base_control.yaml'))
                if name=='orin_return_no_motion':
                    bridge=next(n for n in nodes if n['package']=='p0_base_bridge')
                    self.assertIs(bridge['parameters'][1]['motion_commands_enabled'],False)
                    self.assertIs(bridge['parameters'][1]['wheel_mapping_confirmed'],False)
                    self.assertEqual(bridge['parameters'][1]['wheel_target_limit_mmps'],0)


if __name__=='__main__':unittest.main()
