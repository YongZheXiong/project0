# ROS 2 工作区

本目录包含 [v1.1.3](../docs/releases/v1.1.3.md) 发布的六个 ROS 2 Humble 包。Nano 实机完成六包构建及五节点隔离运行，另用软件替身消息验证了模式与末端指令仲裁。真实手柄和旧轮组的架空证据见[验证报告](../reports/nano_h60_raised_control_v1_1_3.md)。

| 包 | 职责 |
| --- | --- |
| `p0_interfaces` | 定义底盘、模式状态及模式和运动锁服务。 |
| `p0_system_manager` | 管理待机、手动与故障状态，通过新许可标识约束恢复。 |
| `p0_manual_control` | 读取 Linux 手柄输入，处理回中、使能键与输入到期。 |
| `p0_safety_manager` | 核对底盘可用性、新鲜模式许可和命令，执行软件停止与锁止。 |
| `p0_base_bridge` | 实现 H60 版本化二进制协议和工程轮端计数观察。 |
| `p0_bringup` | 提供组合启动与默认参数。 |

默认配置的 `motion_commands_enabled`、`wheel_mapping_confirmed` 为 `false`，`wheel_target_limit_mmps` 为 `0`。隔离启动使用不存在的输入和串口端点。当前 Nano 架空试验采用 USB-COM 和独立映射，仓库默认串口 `/dev/ttyTHS1` 为此前的板载串口配置项。生产轮组参数与里程计仍待。

## 无设备测试

在仓库根目录运行。每包独立发现测试，避免不同包中的同名测试文件冲突。需要 Python 3.9 或更新版本。

```sh
export PYTHONPATH=src/p0_base_bridge:src/p0_manual_control:src/p0_safety_manager:src/p0_system_manager
for package in p0_base_bridge p0_manual_control p0_safety_manager p0_system_manager p0_bringup; do
  python3 -m unittest discover -s "src/$package/test" -q || exit 1
done
```

在 Ubuntu 22.04 和 ROS 2 Humble 环境可构建并检查隔离图。让示例端点保持缺席。

```sh
. /opt/ros/humble/setup.sh
colcon build --base-paths src
. install/setup.sh
ROS_LOCALHOST_ONLY=1 ros2 launch p0_bringup orin_return_no_motion.launch.py
```
