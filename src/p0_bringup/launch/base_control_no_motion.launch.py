"""Start the stage-E prerequisite graph in its default no-motion state."""

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import os


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("p0_bringup"), "config", "base_control.yaml"
    )
    return LaunchDescription(
        [
            Node(
                package="p0_manual_control",
                executable="linux_joy",
                name="p0_linux_joy",
                output="screen",
                parameters=[config],
            ),
            Node(
                package="p0_base_bridge",
                executable="base_bridge",
                name="p0_base_bridge",
                output="screen",
                parameters=[config],
            ),
            Node(
                package="p0_safety_manager",
                executable="command_arbiter",
                name="p0_safety_manager",
                output="screen",
                parameters=[config],
            ),
            Node(
                package="p0_manual_control",
                executable="joy_adapter",
                name="p0_manual_control",
                output="screen",
                parameters=[config],
            ),
        ]
    )
