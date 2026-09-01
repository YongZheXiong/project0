# ROS2 Source Workspace

`src/` 是 Project0 的 ROS2 Humble 源码包入口。当前已提供 H60 迁移的离线实现：

> `p0_base_bridge` 活动节点现使用 H60 版本化二进制协议、原始字节串口、STOP、新会话心跳、输入回中、显式 ARM、A-D 遥测和 ACK/NACK；`p0_safety_manager` 使用 `motion_ready` 和软件运动锁。默认配置保持 `motion_commands_enabled=false`、`wheel_mapping_confirmed=false`、`wheel_target_limit_mmps=0`，H60 `v0.1.1` 还固定报告运动输出不可用，所以本代码不能申请 ARM。旧 STM32 文本解析、16-bit 解绕、CPR 和 `ESTOP` 字段仅作历史兼容，不参与活动路径。本轮仅有 Mac 离线测试，不表示 Orin ROS2 构建、UART 实机、H4/H5、接电机或运动通过。

| 包 | 职责 | 当前边界 |
| --- | --- | --- |
| `p0_interfaces` | 底盘指令、H60 状态和运动锁服务 | `ChassisStatus` 已新增协议/固件版本、状态机、VIN、故障和 A-D 原始计数；旧 LF/RF 与 ESTOP 字段保持中性兼容 |
| `p0_base_bridge` | ROS2 到 H60 `/dev/ttyTHS1` 的二进制桥 | 离线实现已完成；A-D 映射、方向、CPR、轮径、Orin ROS2/H60 实机和单侧掉电反供电仍未验证，默认双门关闭 |
| `p0_safety_manager` | 通信/运动就绪、软件运动锁、手动/自动命令仲裁 | `/p0/motion/stop` 与 `/p0/motion/clear_lock` 已取代活动运行路径中的旧软件急停服务；清锁不自动 ARM |
| `p0_manual_control` | Flydigi Linux joystick 动态发现、无线心跳与 `sensor_msgs/Joy` 手动指令适配 | 真实映射和关机断开清零已无动力复验 |
| `p0_bringup` | 安全默认的组合启动和参数 | `base_control_no_motion.launch.py` 默认不产生活动运动指令 |

本机可运行不依赖 ROS2 的协议、串口、会话门控和仲裁单元测试。旧 STM32 平台的通信、计数解绕与 RR 失计只作为历史兼容背景，不是当前 H60 P2 阻塞。

`package.xml` 中的 `0.1.0` 是各 ROS2 包自身的历史包版本，不是 Project0 项目发布版本，不参与 P0–P10 的 `v0.1`–`v2.4` 映射。
