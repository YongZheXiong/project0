"""Start the Orin return graph with physical inputs deliberately isolated."""

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("p0_bringup"), "config", "base_control.yaml"
    )
    serial_device = LaunchConfiguration("serial_device")
    joystick_device = LaunchConfiguration("joystick_device")
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "serial_device",
                default_value="/dev/project0_h60_isolated",
                description="Deliberately nonexistent H60 path; never use a real endpoint here.",
            ),
            DeclareLaunchArgument(
                "joystick_device",
                default_value="/dev/project0_joystick_isolated",
                description="Deliberately nonexistent joystick path for bounded smoke startup.",
            ),
            Node(
                package="p0_system_manager",
                executable="system_manager",
                name="p0_system_manager",
                output="screen",
                parameters=[config],
            ),
            Node(
                package="p0_manual_control",
                executable="linux_joy",
                name="p0_linux_joy",
                output="screen",
                parameters=[config, {"device_path": joystick_device}],
            ),
            Node(
                package="p0_base_bridge",
                executable="base_bridge",
                name="p0_base_bridge",
                output="screen",
                parameters=[
                    config,
                    {
                        "serial_device": serial_device,
                        "motion_commands_enabled": False,
                        "wheel_mapping_confirmed": False,
                        "wheel_target_limit_mmps": 0,
                    },
                ],
            ),
            Node(
                package="p0_safety_manager",
                executable="command_arbiter",
                name="p0_safety_manager",
                output="screen",
                parameters=[config, {"autonomy_enabled": False}],
            ),
            Node(
                package="p0_manual_control",
                executable="joy_adapter",
                name="p0_manual_control",
                output="screen",
                parameters=[config, {"mapping_confirmed": False}],
            ),
        ]
    )
