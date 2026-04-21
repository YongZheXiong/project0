# 项目0（Project Zero）

## 项目概述

项目0是一个单人solo开发的具身智能小车平台项目，面向广东工业大学教学楼单层回字形走廊真实场景，目标是构建一个具备感知—决策—执行闭环、语义导航能力、安全约束机制的类产品级基础平台，并在此基础上进行能力增强与科研验证。

## 当前状态

| 项目 | 状态 |
|------|------|
| 当前阶段 | P1：功能落地、技术选型与工程准备 |
| 当前版本 | V0.2.2 |
| 最近更新 | 新增了 interface_definition.md |

## 硬件平台
- 计算：Jetson Orin NX 16GB
- 下位机：STM32F407ZGT6
- 激光雷达：Livox Mid-360
- 深度相机：Intel RealSense D435
- 底盘：四轮差速（GB37-555 ×4）

## 快速开始

## 目录结构
```text
project0/
├── docs/                   # 文档
│   ├── 00_definition/      # P0：项目定义
│   ├── 01_planning/        # P1：功能与选型
│   ├── 02_architecture/    # P1：架构设计
│   ├── 03_design/          # P2+：模块详设
│   ├── 04_deployment/      # 部署说明
│   ├── 05_calibration/     # 标定记录
│   ├── 06_testing/         # 测试
│   └── 07_iter2/           # 迭代二文档
├── hardware/               # 硬件
├── firmware/               # STM32固件
├── src/                    # ROS2源码
├── config/                 # 配置
├── scripts/                # 脚本
├── data/                   # 运行数据
├── experiments/            # 实验
├── simulation/             # 仿真
├── reports/                # 报告
├── presentation/           # 展示与答辩
└── process/                # 过程沉淀
|   ├── decisions/          # 决策记录
|   ├── learning_notes/
|   └── weekly_log/         # 周记
├── README.md
├── LICENSE
├── CHANGELOG.md
└── .gitignore
```

---

## 版本记录
见 CHANGELOG.md

## 作者
Xiong Yongzhe