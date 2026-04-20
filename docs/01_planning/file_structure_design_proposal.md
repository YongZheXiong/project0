# 项目0 完整文件结构设计方案

---

## 一、英文命名版目录树（主版本，Git仓库实际使用）

```
project0/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── .gitignore
│
├── docs/                                   # 【文档层】全部文档
│   ├── 00_definition/                      # P0：项目定义文件集
|   |   ├── project_workflow.md             # 项目流程
│   │   ├── system_positioning.md           # 最终系统定位
│   │   ├── objective_constraints.md        # 客观限制
│   │   ├── subjective_requirements.md      # 主观需求
│   │   ├── iter1_core_capabilities.md      # 迭代一核心能力
│   │   ├── iter2_enhancement_scope.md      # 迭代二增强能力
│   │   ├── overall_deliverables.md         # 整体成果形态
│   │   ├── version_roadmap.md              # 版本线路图
│   │   └── milestone_timeline.md           # 里程碑时间表
│   │
│   ├── 01_planning/                        # P1：功能落地与技术选型
│   │   ├── iter1_function_list.md          # 迭代一功能清单与技术选型表
│   │   ├── iter1_function_items.md         # 迭代一功能条目展开表
│   │   ├── wbs.md                          # WBS
│   │   ├── sprint_plan.md                  # Sprint规划
│   │   └── procurement_list.md             # 采购清单
│   │
│   ├── 02_architecture/                    # P1：系统架构设计
│   │   ├── system_architecture.md          # 系统总架构
│   │   ├── compute_comm_architecture.md    # 计算与通信架构
│   │   ├── power_architecture.md           # 电源架构
│   │   ├── hardware_architecture.md        # 硬件架构
│   │   ├── software_architecture.md        # 软件架构与数据流
│   │   ├── interface_definition.md         # 接口定义表
│   │   ├── wiring_diagram.md               # 接线图
│   │   └── diagrams/                       # 架构图源文件
│   │       ├── system_arch.drawio
│   │       └── data_flow.drawio
│   │
│   ├── 03_design/                          # P2-P6：各模块详细设计（逐步建立）
│   │   ├── chassis_motion.md
│   │   ├── perception_sensors.md
│   │   ├── slam_localization.md
│   │   ├── navigation_obstacle.md
│   │   ├── semantic_navigation.md
│   │   ├── task_scheduler.md
│   │   ├── safety_mechanism.md
│   │   └── system_management.md
│   │
│   ├── 04_deployment/                      # 环境部署与运行说明
│   │   ├── orin_nx_setup.md                # Orin NX环境部署
│   │   ├── stm32_setup.md                  # STM32开发环境
│   │   ├── ros2_workspace_setup.md         # ROS2 workspace搭建
│   │   ├── remote_dev_setup.md             # 远程开发方案
│   │   └── run_instructions.md             # 运行说明（从零到可运行）
│   │
│   ├── 05_calibration/                     # 标定记录（P2-P3建立）
│   │   ├── sensor_extrinsics.yaml
│   │   ├── imu_calibration.md
│   │   ├── camera_intrinsics.yaml
│   │   └── encoder_calibration.md
│   │
│   ├── 06_testing/                         # 【测试层】测试计划与记录
│   │   ├── test_plan_iter1.md              # 迭代一测试计划
│   │   ├── acceptance_criteria_iter1.md    # 迭代一验收标准
│   │   ├── test_scenarios/                 # 测试场景清单
│   │   │   ├── P2_chassis_tests.md
│   │   │   ├── P3_perception_tests.md
│   │   │   ├── P4_navigation_tests.md
│   │   │   ├── P5_semantic_tests.md
│   │   │   ├── P6_integration_tests.md
│   │   │   └── P6_safety_tests.md
│   │   ├── test_results/                   # 测试结果记录
│   │   │   ├── 20250101_P2_motor_pid_test.md
│   │   │   └── ...
│   │   └── regression/                     # 回归测试（P6+建立）
│   │       └── regression_checklist.md
│   │
│   └── 07_iter2/                           # 迭代二专用文档（P7+建立）
│       ├── enhancement_plan.md             # 增强方案设计
│       ├── experiment_design.md            # 实验设计
│       ├── baseline_data.md                # 性能基线
│       ├── ablation_design.md              # 消融实验设计
│       └── iter2_test_plan.md
│
├── hardware/                               # 【硬件层】
│   ├── bom.csv                             # 物料清单
│   ├── wiring/                             # 接线图/原理图
│   │   └── main_wiring.pdf
│   ├── mechanical/                         # 机械结构（如有3D模型）
│   │   └── chassis_layout.step
│   └── photos/                             # 硬件实物照片
│       └── README.md                       # 照片索引说明
│
├── firmware/                               # 【固件层】STM32代码
│   ├── README.md
│   ├── Core/
│   │   ├── Inc/
│   │   └── Src/
│   ├── Drivers/
│   ├── Middlewares/                         # 如使用FreeRTOS等
│   ├── project0_firmware.ioc               # CubeMX工程文件
│   └── CMakeLists.txt                      # 或Makefile
│
├── src/                                    # 【ROS2软件层】ROS2 workspace的src
│   ├── project0_bringup/                   # 启动管理包
│   │   ├── launch/
│   │   │   ├── bringup_all.launch.py
│   │   │   ├── chassis_only.launch.py
│   │   │   ├── slam_mapping.launch.py
│   │   │   ├── navigation.launch.py
│   │   │   └── record_bag.launch.py
│   │   ├── config/                         # → 指向或包含配置
│   │   └── package.xml
│   │
│   ├── project0_base/                      # 底盘驱动与里程计
│   │   ├── src/
│   │   ├── include/
│   │   ├── config/
│   │   └── package.xml
│   │
│   ├── project0_perception/                # 传感器驱动与预处理
│   │   ├── src/
│   │   ├── config/
│   │   └── package.xml
│   │
│   ├── project0_slam/                      # SLAM与定位
│   │   ├── config/
│   │   ├── launch/
│   │   └── package.xml
│   │
│   ├── project0_navigation/                # Nav2导航与避障
│   │   ├── config/
│   │   ├── launch/
│   │   ├── maps/                           # 地图文件
│   │   │   ├── corridor_floor1.yaml
│   │   │   └── corridor_floor1.pgm
│   │   └── package.xml
│   │
│   ├── project0_semantic/                  # 语义导航与目标管理
│   │   ├── config/
│   │   │   └── semantic_locations.yaml     # 语义地点注册表
│   │   ├── src/
│   │   └── package.xml
│   │
│   ├── project0_task/                      # 任务状态机与调度
│   │   ├── src/
│   │   └── package.xml
│   │
│   ├── project0_safety/                    # 安全机制
│   │   ├── src/
│   │   ├── config/
│   │   │   └── forbidden_zones.yaml        # 禁区配置
│   │   └── package.xml
│   │
│   ├── project0_monitor/                   # 系统监控与自检
│   │   ├── src/
│   │   └── package.xml
│   │
│   ├── project0_description/               # URDF模型
│   │   ├── urdf/
│   │   ├── meshes/
│   │   └── package.xml
│   │
│   └── project0_msgs/                      # 自定义消息/服务/动作
│       ├── msg/
│       ├── srv/
│       ├── action/
│       └── package.xml
│
├── config/                                 # 【配置层】全局配置汇总
│   ├── nav2_params.yaml
│   ├── cartographer.lua
│   ├── ekf_params.yaml
│   ├── serial_params.yaml
│   └── system_params.yaml
│
├── scripts/                                # 【脚本层】工具脚本
│   ├── setup_env.sh                        # 环境初始化
│   ├── start_all.sh                        # 一键启动
│   ├── stop_all.sh                         # 优雅关闭
│   ├── self_check.sh                       # 系统自检
│   ├── record_bag.sh                       # 数据录制快捷脚本
│   └── utils/
│       ├── plot_trajectory.py              # 轨迹可视化
│       ├── analyze_bag.py                  # bag数据分析
│       └── export_metrics.py              # 指标导出
│
├── data/                                   # 【数据层】运行数据（大文件不入Git）
│   ├── README.md                           # 数据目录说明与索引
│   ├── bags/                               # rosbag2录制文件
│   │   └── 20250701_corridor_exp01/
│   ├── maps/                               # 建图结果归档
│   │   └── 20250701_corridor_v1/
│   ├── logs/                               # 结构化运行日志
│   │   └── 20250701_run01.json
│   └── calibration_data/                   # 标定原始数据
│
├── experiments/                            # 【实验层】
│   ├── README.md                           # 实验总索引
│   ├── exp001_pid_tuning/                  # 实验编号_简述
│   │   ├── design.md                       # 实验设计
│   │   ├── procedure.md                    # 实验步骤
│   │   ├── raw_data/                       # → 指向data/或本地小文件
│   │   ├── results/                        # 结果图表
│   │   │   ├── speed_response.png
│   │   │   └── metrics.csv
│   │   └── conclusion.md                   # 结论
│   ├── exp002_slam_corridor/
│   └── ...
│
├── simulation/                             # 仿真环境（P1建立，辅助用）
│   ├── worlds/
│   │   └── corridor_simple.world
│   ├── models/
│   └── launch/
│       └── sim_bringup.launch.py
│
├── reports/                                # 【报告层】
│   ├── iter1_platform_report/              # 迭代一平台报告
│   │   ├── main.md                         # 或 main.tex
│   │   ├── figures/
│   │   └── tables/
│   ├── iter2_enhancement_report/           # 迭代二实验报告（P8+建立）
│   │   ├── front_slam_report.md
│   │   └── rear_semantic_report.md
│   └── final_report/                       # 类论文式总报告（P10建立）
│       ├── main.md
│       ├── figures/
│       └── references.bib
│
├── presentation/                           # 【展示与答辩层】
│   ├── demo_videos/                        # 演示视频（大文件不入Git）
│   │   └── README.md                       # 视频索引与网盘链接
│   ├── screenshots/                        # 运行截图
│   ├── one_pager.md                        # 项目一页纸简介
│   ├── defense_ppt/                        # 答辩PPT
│   │   └── project0_defense_v1.pptx
│   ├── defense_qa.md                       # 答辩问答准备
│   ├── highlights.md                       # 项目亮点总结
│   └── demo_script.md                      # 演示脚本
│
├── process/                                # 【过程沉淀层】
│   ├── decisions/                          # 决策记录
│   │   ├── DEC-001_slam_selection.md
│   │   ├── DEC-002_comm_protocol.md
│   │   └── ...
│   ├── problem_log/                        # 问题日志
│   │   ├── PRB-001_motor_jitter.md
│   │   └── ...
│   ├── learning_notes/                     # 学习笔记
│   │   ├── ros2_launch_system.md
│   │   ├── pid_tuning_notes.md
│   │   └── ...
│   ├── experiment_log/                     # 实验日志（日常简记）
│   │   ├── 20250701_field_test.md
│   │   └── ...
│   ├── failure_cases/                      # 失败案例集
│   │   └── FAIL-001_localization_drift.md
│   ├── retrospectives/                     # 复盘记录
│   │   ├── P2_retrospective.md
│   │   └── ...
│   └── weekly_log/                         # 周记/进度记录
│       ├── 2025_W27.md
│       └── ...
│
└── .vscode/                                # 开发工具配置（可选）
    ├── settings.json
    └── tasks.json
```

---

## 二、中文命名版目录树（仅供理解对照，不建议实际使用）

```
项目0/
├── 文档/
│   ├── 00_项目定义/
│   ├── 01_规划与选型/
│   ├── 02_系统架构/
│   ├── 03_模块设计/
│   ├── 04_部署说明/
│   ├── 05_标定记录/
│   ├── 06_测试/
│   └── 07_迭代二/
├── 硬件/
├── 固件/
├── 源码（ROS2）/
├── 配置/
├── 脚本/
├── 数据/
├── 实验/
├── 仿真/
├── 报告/
├── 展示与答辩/
└── 过程沉淀/
    ├── 决策记录/
    ├── 问题日志/
    ├── 学习笔记/
    ├── 失败案例/
    ├── 复盘记录/
    └── 周记/
```

**建议：Git仓库统一使用英文命名版。** 中文版仅作为你理解目录含义的参照。

---

## 三、各阶段建立时机

### P0/P1 必须建立

| 目录 | 说明 |
|------|------|
| `docs/00_definition/` | 锁定六份定义文件 [3] |
| `docs/01_planning/` | 功能清单、WBS、采购清单 [5] |
| `docs/02_architecture/` | 系统架构设计 [5] |
| `docs/04_deployment/` | 环境部署说明 [5] |
| `firmware/` | STM32工程骨架 |
| `src/` | ROS2 workspace骨架（至少bringup、base、msgs）|
| `config/` | 全局配置目录 |
| `scripts/` | 基础脚本 |
| `process/decisions/` | 开始记录决策 [3] |
| `process/learning_notes/` | 开始记录学习 [3] |
| `process/weekly_log/` | 开始周记 |
| `simulation/` | 仿真基础环境 [5] |
| `README.md` `.gitignore` `CHANGELOG.md` | 仓库基础文件 |

### P2-P6 逐步建立

| 目录 | 建立时机 |
|------|----------|
| `src/project0_perception/` | P3 |
| `src/project0_slam/` | P3 |
| `src/project0_navigation/` | P4 |
| `src/project0_semantic/` | P5 |
| `src/project0_task/` | P5 |
| `src/project0_safety/` | P4-P6 |
| `src/project0_monitor/` | P6 |
| `docs/03_design/` | P2起逐模块补充 |
| `docs/05_calibration/` | P2-P3 |
| `docs/06_testing/` | P2起逐阶段补充 [12] |
| `data/` | P2起首次真机运行时建立 |
| `experiments/` | P2起首个实验时建立 |
| `process/problem_log/` | P2起首次遇到问题时 |
| `process/failure_cases/` | 有失败案例时 |
| `process/retrospectives/` | 每阶段结束时 |
| `hardware/photos/` | P2组装时 |
| `reports/iter1_platform_report/` | P6 [12][13] |
| `presentation/screenshots/` | P2起采集 [3] |

### 迭代二再建立（P7+）

| 目录 | 说明 |
|------|------|
| `docs/07_iter2/` | 增强方案、实验设计、基线数据 [11] |
| `reports/iter2_enhancement_report/` | P8-P9 |
| `reports/final_report/` | P10 [1] |
| `presentation/defense_ppt/` | P10 [1] |
| `presentation/demo_videos/` | P10最终版（过程中素材先放screenshots）|
| `presentation/defense_qa.md` | P10 [1][7] |

---

## 四、关键目录内容说明

| 一级目录 | 放什么 |
|----------|--------|
| `docs/` | 所有非代码文档：定义、规划、架构、设计、部署、标定、测试 [2][7] |
| `hardware/` | BOM、接线图PDF、机械图、实物照片 [5] |
| `firmware/` | STM32全部固件代码，CubeMX工程 [15] |
| `src/` | ROS2所有功能包，按职责拆包 [5][15] |
| `config/` | 全局参数YAML/Lua，与launch配合 [9] |
| `scripts/` | Shell/Python工具脚本，启动、自检、数据分析 [9] |
| `data/` | rosbag、地图文件、日志、标定数据（大文件）[9] |
| `experiments/` | 按实验编号组织，每个实验含设计-数据-结果-结论 [7] |
| `simulation/` | Gazebo世界、模型、仿真launch [5] |
| `reports/` | 迭代一报告、迭代二报告、总报告 [1][13] |
| `presentation/` | 视频、PPT、一页纸、答辩QA、亮点总结 [1][7] |
| `process/` | 决策记录、问题日志、学习笔记、失败案例、复盘、周记 [2][3] |

---

## 五、命名规范

### 5.1 文档编号规则

| 类型 | 格式 | 示例 |
|------|------|------|
| 决策记录 | `DEC-XXX_简述.md` | `DEC-001_slam_selection.md` |
| 问题日志 | `PRB-XXX_简述.md` | `PRB-003_serial_timeout.md` |
| 失败案例 | `FAIL-XXX_简述.md` | `FAIL-002_nav_stuck_corner.md` |

### 5.2 实验目录命名

```
expXXX_简述/
```
示例：`exp001_pid_tuning/`、`exp005_slam_loop_closure/`、`exp010_iter2_fusion_compare/`

### 5.3 数据文件命名

```
YYYYMMDD_场景_实验编号/
```
示例：`20250715_corridor_3F_exp003/` [9]

### 5.4 测试记录命名

```
YYYYMMDD_阶段_测试内容.md
```
示例：`20250710_P2_motor_pid_test.md`

### 5.5 过程文档命名

| 类型 | 格式 |
|------|------|
| 周记 | `YYYY_WXX.md`（如`2025_W27.md`）|
| 复盘 | `PX_retrospective.md` |
| 学习笔记 | `主题名.md`（如`cartographer_tuning.md`）|

### 5.6 Git标签

| 标签 | 对应阶段 |
|------|----------|
| `V0.1` | P0-P1完成 [9] |
| `V0.2`-`V0.9` | P2-P5各阶段 |
| `V1.0` | 迭代一验收通过 [9][12] |
| `V2.0-alpha` | 迭代二前段完成 [11] |
| `V2.0` | 迭代二完成 [9][11] |

---

## 六、Git管理策略

### 纳入Git

- 所有代码（`firmware/`、`src/`）
- 所有配置（`config/`）
- 所有脚本（`scripts/`）
- 所有文档（`docs/`）
- 所有过程沉淀（`process/`）
- 报告源文件（`reports/`）
- 展示材料文本类（`presentation/`中的md文件）
- 实验设计与结论（`experiments/*/design.md`、`conclusion.md`）
- `data/README.md`（索引）
- 小体积地图文件（`.yaml` + `.pgm`）

### 不入Git（.gitignore + 索引说明）

- `data/bags/` — rosbag文件，通常数GB [9]
- `data/logs/` — 大量运行日志
- `data/calibration_data/` — 标定原始数据
- `presentation/demo_videos/` — 视频文件
- `hardware/mechanical/*.step` — 大型CAD文件
- `build/`、`install/`、`log/` — ROS2编译产物
- `__pycache__/`、`*.pyc`
- `.vscode/` 中的个人配置（可选入）

这些目录下放 `README.md` 写明：文件说明、存储位置（网盘链接）、文件列表。

---

## 七、.gitignore 建议

```gitignore
# ROS2 build
build/
install/
log/

# Python
__pycache__/
*.pyc
*.pyo

# Data (large files)
data/bags/
data/logs/
data/calibration_data/

# Videos
presentation/demo_videos/*.mp4
presentation/demo_videos/*.mkv

# CAD
hardware/mechanical/*.step
hardware/mechanical/*.stl

# OS
.DS_Store
Thumbs.db

# IDE
.idea/
*.swp
*.swo

# Compiled firmware
firmware/build/
firmware/Debug/
firmware/Release/
```

---

## 八、README.md 建议结构

```markdown
# Project0 — 地面移动具身智能平台

## 项目简介
面向教学楼室内走廊场景的具身智能小车平台，具备感知—定位—导航—语义理解—安全保护闭环能力。

## 项目状态
当前阶段：P1 / 版本：V0.1

## 硬件平台
- 计算：Jetson Orin NX 16GB
- 下位机：STM32F407ZGT6
- 激光雷达：Livox Mid-360
- 深度相机：Intel RealSense D435
- 底盘：四轮差速（GB37-555 ×4）

## 快速开始
1. 环境部署：见 `docs/04_deployment/`
2. 编译：`colcon build`
3. 启动：`bash scripts/start_all.sh`

## 目录结构
（简要列出一级目录及说明）

## 版本记录
见 CHANGELOG.md

## 作者
XXX / 广东工业大学
```

---

## 九、LICENSE 与 CHANGELOG

**LICENSE**：建议建立。推荐 `MIT` 或 `Apache-2.0`。即使暂时不开源，有LICENSE体现工程规范性，复试展示时加分。

**CHANGELOG.md**：强烈建议建立。格式：

```markdown
# Changelog

## [V0.1] - 2025-07-XX
### 完成
- P0项目定义锁定
- P1功能清单与技术选型完成
- Git仓库与目录结构建立

## [V0.2] - 2025-XX-XX
### 完成
- P2底盘运动闭环成立
```

每个Git tag对应一条CHANGELOG条目，与版本线路图对齐 [9][12]。

---

**总结**：以上结构覆盖了你项目的六条主线（定义规划 + 工程实现 + 数据实验 + 测试验收 + 过程沉淀 + 成果表达）[2][7][10]，按阶段渐进建立，单人可维护，直接照着建即可。