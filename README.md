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


## 版本记录
见 CHANGELOG.md

## 作者
xiongyongzhe / GDUT