# Project0

Project0 是一个单人开发的具身智能小车平台项目，面向室内单层回字形走廊真实场景，目标是构建具备感知、决策、执行闭环和安全约束机制的地面移动机器人基础平台。

项目当前以真机平台为主线，优先完成可运行、可验证、可迭代的第一版系统，再在此基础上继续增强定位、导航、语义任务和实验支撑能力。

## 当前状态

| 项目 | 状态 |
| --- | --- |
| 当前阶段 | P2：P1 已正式结束；进入底盘装配、电气安全边界和基础运动验证阶段 |
| 当前目标 | 完成 STM32 替换板验收并恢复 UART、编码器和基础运动验证 |
| ROS2 基线 | ROS2 Humble 基础环境与 `~/project0_ros2_ws` 工作区骨架已完成最小验证 |
| STM32 基线 | CMSIS-DAP / OpenOCD 路径已验证；原控制板发生 3.3V 供电故障，待替换板验收 |
| 规划基线 | P2-P6 WBS、P2 Sprint 和迭代一风险登记已形成公开版基线 |

## 硬件摘要

| 类别 | 当前选型 |
| --- | --- |
| 主计算 | Jetson Orin NX 16GB |
| 激光雷达 | Livox Mid360 |
| 深度相机 | Intel RealSense D435 |
| 底盘 | 四轮差速，JGB-520 电机 x 4 |
| 结构 | 三层底盘结构方案 |

当前状态表示 P1 到货与工程准备验收已完成，并不表示 P2 已完成。急停动力切断已完成基础验证，但 UART、编码器、落地运动、FAST-LIO2、Nav2、Livox、RealSense、正式 ROS2 功能包和正式 STM32 固件仍会随项目推进继续更新。

P1.4 当前为最小工程环境收束：仿真基础环境和完整远程调试方案按条件触发后置，不作为 P2 前置条件。当前远程访问已确认 SSH 可用，后续调试方案按真实开发需要再补。

## 公开目录

```text
Project0/
├── config/              # 配置文件
├── data/                # 数据目录
├── docs/
│   ├── 01_planning/     # 公开版 WBS、Sprint 和风险登记
│   ├── 02_architecture/ # 系统、软硬件、通信、电源与接口架构
│   └── 04_deployment/   # Orin NX、ROS2、STM32 等部署记录
├── firmware/            # STM32 / 底层固件
├── hardware/            # BOM、结构、线束和硬件资料
├── presentation/        # 展示材料
├── reports/             # 报告材料
├── scripts/             # 工具脚本
├── simulation/          # 仿真资料
├── src/                 # ROS2 源码
├── LICENSE
└── README.md
```

## 文档入口

- `docs/02_architecture/`：系统架构、计算通信架构、软件架构、硬件架构、电源架构和接口定义。
- `docs/01_planning/`：公开版迭代一 WBS、Sprint 规划和风险登记。
- `docs/04_deployment/`：Orin NX 基线、ROS2 环境、ROS2 工作区、STM32 工具链和后续部署记录。
- `hardware/`：公开硬件资料、BOM、线束记录和 CAD 资料。
- `reports/`：可公开的测试与验收报告。
- `scripts/`：可复跑的工程和测试脚本。

## 开发与运行

当前 ROS2 基础环境记录见：

```text
docs/04_deployment/ros2_workspace_setup.md
```

当前 Orin NX 实机基线记录见：

```text
docs/04_deployment/orin_nx_setup.md
```

当前 STM32 环境记录见：

```text
docs/04_deployment/stm32_setup.md
```

后续会继续补充底层通信、传感器驱动、SLAM、导航和系统启动流程。
