# Project0

Project0 是一个单人开发的具身智能小车平台项目，面向室内单层回字形走廊真实场景，目标是构建具备感知、决策、执行闭环和安全约束机制的地面移动机器人基础平台。

项目当前以真机平台为主线，优先完成可运行、可验证、可迭代的第一版系统，再在此基础上继续增强定位、导航、语义任务和实验支撑能力。

## 当前状态

| 项目 | 状态 |
| --- | --- |
| 当前阶段 | P1.4：工程环境搭建已完成最小收束；P1.3 到货验收与 P2 装配前置继续并行承接 |
| 当前目标 | 在 Orin NX、ROS2 工作区和 STM32 工具链的最小环境基线上，继续准备后续机械 / 电气装配验证 |
| ROS2 基线 | ROS2 Humble 基础环境与 `~/project0_ros2_ws` 工作区骨架已完成最小验证 |
| STM32 基线 | STM32 工具链、USB 设备识别、最小工程编译复验和 ST-LINK 通道边界已记录 |

## 硬件摘要

| 类别 | 当前选型 |
| --- | --- |
| 主计算 | Jetson Orin NX 16GB |
| 激光雷达 | Livox Mid360 |
| 深度相机 | Intel RealSense D435 |
| 底盘 | 四轮差速，JGB-520 电机 x 4 |
| 结构 | 三层底盘结构方案 |

当前状态不表示整车已经完成装配、接线、上电或验收，也不表示 FAST-LIO2、Nav2、Livox、RealSense、正式 ROS2 功能包或正式 STM32 固件已经完成。硬件和部署记录会随项目推进继续更新。

## 公开目录

```text
Project0/
├── config/              # 配置文件
├── data/                # 数据目录
├── docs/
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
- `docs/04_deployment/`：Orin NX 基线、ROS2 环境、ROS2 工作区、STM32 工具链和后续部署记录。
- `hardware/`：公开硬件资料、BOM、线束记录和 CAD 资料。

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
