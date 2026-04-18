# 项目0（Project Zero）

> 面向教学楼走廊场景的具身智能地面移动平台

## 项目概述

项目0是一个单人solo开发的具身智能小车平台项目，面向广东工业大学教学楼单层回字形走廊真实场景，目标是构建一个具备感知—决策—执行闭环、语义导航能力、安全约束机制的类产品级基础平台，并在此基础上进行能力增强与科研验证。

## 当前状态

| 项目 | 状态 |
|------|------|
| 当前阶段 | P1：功能落地、技术选型与工程准备 |
| 当前版本 | V0.1（前置准备阶段） |
| 最近更新 | 软件架构、信息流文档完成 |

## 项目结构

project0/
├── docs/
│   ├── definition/                      # P0 项目定义文档
│   │   ├── system_positioning.md        # 最终系统定位
│   │   ├── objective_constraints.md     # 客观限制
│   │   ├── subjective_requirements.md   # 主观需求
│   │   ├── iter1_core_capabilities.md   # 迭代一核心能力
│   │   ├── iter2_enhancement_scope.md   # 迭代二增强能力
│   │   └── overall_deliverables.md      # 整体成果形态
│   ├── architecture/                    # 架构文档
│   │   ├── system_architecture.md       # 系统总架构
│   │   ├── software_architecture.md     # 软件架构
│   │   └── information_flow.md          # 信息流设计
│   ├── workflow/                        # 流程与规划
│   │   ├── project_workflow.md          # 项目流程（第二版）
│   │   ├── milestone_timeline.md        # 里程碑时间表
│   │   ├── iter1_function_items.md      # 迭代一功能条目展开
│   │   └── iter1_function_list.md       # 迭代一功能清单与技术选型
│   └── logs/                            # 过程记录
│       └── sync_log.md                  # 同步与更新记录
├── src/                                 # 源代码（P2开始）
├── config/                              # 配置文件（P2开始）
├── scripts/                             # 脚本工具
├── media/                               # 素材（视频、截图、P2开始采集）
└── README.md


## 文档索引

### P0 项目定义（已锁定）

| 文档 | 路径 | 说明 |
|------|------|------|
| 最终系统定位 | `docs/definition/system_positioning.md` | 项目场景、平台定位 |
| 客观限制 | `docs/definition/objective_constraints.md` | 硬件、场地、人力等约束 |
| 主观需求 | `docs/definition/subjective_requirements.md` | 个人目标与项目要求 |
| 迭代一核心能力 | `docs/definition/iter1_core_capabilities.md` | 十项核心能力定义 |
| 迭代二增强能力 | `docs/definition/iter2_enhancement_scope.md` | 增强方向与分阶段策略 |
| 整体成果形态 | `docs/definition/overall_deliverables.md` | 成果体系定义 |

### P1 架构与选型（进行中）

| 文档              | 路径                                           | 说明              | 状态   |
| --------------- | -------------------------------------------- | --------------- | ---- |
| 功能条目展开          | `docs/workflow/iter1_function_items.md`      | 十项能力拆解为中粒度功能条目  | ✅ 完成 |
| 功能清单与技术选型       | `docs/workflow/iter1_function_list.md`       | 功能清单与技术选型表      | ✅ 完成 |
| 系统总架构           | `docs/architecture/system_architecture.md`   | 八模块划分与主辅链路设计    | ✅ 完成 |
| 软件架构            | `docs/architecture/software_architecture.md` | ROS 2 包划分与节点规划  | ✅ 完成 |
| 信息流设计           | `docs/architecture/information_flow.md`      | 话题、服务与核心数据流设计   | ✅ 完成 |
| 项目流程            | `docs/workflow/project_workflow.md`          | P0 到 P10 全阶段流程  | ✅ 完成 |
| 里程碑时间表          | `docs/workflow/milestone_timeline.md`        | M1、M2、M3 时间节点规划 | ✅ 完成 |
| 硬件方案与 BOM       | -                                            | 待启动             | ⬜    |
| 工程环境搭建          | -                                            | 待启动             | ⬜    |
| WBS 与 Sprint 规划 | -                                            | 待启动             | ⬜    |


## 阶段进度

| 阶段 | 名称 | 归属 | 状态 |
|------|------|------|------|
| P0 | 项目定义收束 | 前置准备 | ✅ 完成 |
| P1 | 功能落地、技术选型与工程准备 | 前置准备 | 🔄 进行中 |
| P2 | 底盘与基础运动成立 | 迭代一 | ⬜ |
| P3 | 感知与定位建图成立 | 迭代一 | ⬜ |
| P4 | 导航与避障成立 | 迭代一 | ⬜ |
| P5 | 语义导航与任务调度成立 | 迭代一 | ⬜ |
| P6 | 系统集成与迭代一验收 | 迭代一 | ⬜ |
| P7-P9 | 迭代二增强 | 迭代二 | ⬜ |
| P10 | 实验收束与成果表达 | 收束 | ⬜ |

## 里程碑

| 里程碑 | 目标时间 | 内容 |
|--------|----------|------|
| M1 | 大三上之前 | 迭代一完成，平台最小闭环成立 |
| M2 | 考研前 | 迭代二完成，能力增强+科研验证 |
| M3 | 复试前 | 项目整体收束，报告/PPT/视频/答辩 |

## 技术栈

- **计算平台**: Jetson Orin NX + STM32
- **传感器**: Livox Mid-360, Intel RealSense D435, IMU, 编码器
- **软件框架**: ROS2 Humble, Ubuntu 22.04
- **核心算法**: FAST-LIO2 (SLAM), Nav2 (导航)
- **语义导航**: YAML语义位置表 + 字符串匹配（迭代一）

## 系统架构概要

**主链路**: 执行层 → 感知层 → 空间认知层 → 行动规划层 → 任务决策层（闭环）

**辅助链路**: 安全保障 | 系统管理 | 数据记录

**软件包**: p0_base_bridge, p0_sensor_drivers, p0_localization, p0_mapping, p0_map_manager, p0_navigation, p0_semantic_nav, p0_task_manager, p0_safety_manager, p0_system_manager, p0_bringup, p0_data_tools, p0_interfaces

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| V0.1 | 当前 | P0-P1前半段完成，定义+架构+选型文档就绪 |
| V1.0 | 计划 | 迭代一验收通过 |
| V2.0 | 计划 | 迭代二完成 |