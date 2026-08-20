# Project0

Project0 是一个面向室内走廊场景的四轮差速移动机器人项目，由个人完成机械、电气、底层控制、ROS2 软件与系统验收。项目以真机为主线，目标是形成可验证的感知—决策—执行闭环，依次完成基础运动、定位建图、导航和最小语义任务，并以完整项目报告收束成果。

## 项目目标

- 在固定室内走廊中建立可复现的单车系统基线。
- 让底盘、传感器、计算平台和 ROS2 软件形成真实闭环。
- 以分阶段验收记录机械、电气、通信、控制、感知和导航结果。
- 保留代码、配置、CAD、接线、测试与失败证据，支持复现和复盘。

## 当前进展

截至 2026-08-20，项目处于 H60 + MC520 底盘重建阶段。

| 项目 | 当前状态 |
| --- | --- |
| 阶段与版本 | P2 / `v1.1-dev` / Unreleased |
| 阶段门 | H0-H8 均为 `NOT RUN`；当前尚未开放上电、刷写或运动 |
| 机械 | 28 个当前整车 STEP 已完成第二轮数字复审；两层铝板、D435 支架和 Mid360 承载件已委托加工，等待交付、尺寸检查与试装 |
| 固件 | H60 运动控制需求已形成；四路驱动、编码器闭环、故障注入和实物验收尚未完成 |
| ROS2 | 当前仓库保留上一 STM32 平台的迁移骨架；H60 版本化底盘桥接尚待实现 |
| 历史平台 | STM32 + WSDC2412D + JGB37-520 + 三层底盘资料已归档 |

数字复审确认当前 CAD 的 28 个 STEP 均为有效 B-Rep，轴距为 `170 mm`、轮距约 `184.16 mm`，采用 6 根层间支柱，D435 水平安装。加工件到货后仍需按 H1 完成尺寸、孔位、平面度、连接器、风道、线束与维护空间的实物复核。

## 系统组成

| 子系统 | 当前方案 |
| --- | --- |
| 主计算 | Jetson Orin NX 16GB |
| 底层控制 | OpenCTR H60 V3.7 |
| 底盘 | 四轮差速，4 × MC520P56_12V，1:56，65 mm 橡胶轮 |
| 感知 | Livox Mid360 + Intel RealSense D435 |
| 供电 | 3S 电池 → 25A 主保险 → 主开关 → H60、Orin、Mid360 三条独立受保护支路 |
| 电压采样 | H60 `PC0` VIN ADC，多点校准后使用 |
| 通信目标 | Orin ↔ H60 版本化 UART 协议，带会话、序号、状态与故障语义 |

## 开发与验收

当前仓库提供 H60 架构、接线、固件要求、CAD 和 H0-H8 验收基线；经 H5-H7 验收的 H60 动力运行固件与 ROS2 底盘桥接仍在开发中。

物理验证按以下顺序推进：

1. H0 到货与版本核对；
2. H1 不上电机械试装；
3. H2 断电电气检查；
4. H3 分支低能量上电；
5. H4 UART 单侧掉电与反向供电验证；
6. H5 固件故障注入；
7. H6 单通道电机与编码器；
8. H7 四轮架空与电源动态；
9. H8 受控场地落地低速。

当前停车与失能链由上电默认 `DISARMED`、显式 ARM、STOP/DISARM、通信超时、IWDG、异常撤 PWM、人工持续监护和主开关整车断电组成。车辆没有独立急停按钮、继电器或急停 GPIO；H8 仅在 H0-H7 全部通过、场地隔离、低速低加速度、主开关直接可达且操作者持续目视时执行。永久 UART 线束还需先完成任一侧掉电时的反向供电测量。

## 文档与资产入口

- [当前 H60 + MC520 实现基线](docs/02_architecture/p2_h60_rebuild_baseline.md)
- [系统架构](docs/02_architecture/system_architecture.md)
- [电源、运动与采样边界](docs/02_architecture/h60_power_motion_sampling_boundary.md)
- [H60 电源接线](hardware/wiring/h60_power_wiring_v0_2.md)
- [H60 运动控制固件要求](firmware/h60_motion_control_firmware_requirements_v0_2.md)
- [H0-H8 重建验收计划](docs/06_testing/p2_h60_mc520_rebuild_acceptance_plan_2026-08-16.md)
- [当前公开 BOM](hardware/bom.md)
- [当前整车 CAD](hardware/cad/current_vehicle_v0_2/README.md)
- [重建基线报告](reports/h60_mc520_rebuild_baseline_2026-08-16.md)
- [版本记录](CHANGELOG.md)

## 仓库结构

```text
Project0_public/
├── config/       # 配置入口
├── data/         # 数据索引与样例
├── docs/         # 架构、部署、标定与测试文档
├── firmware/     # H60 固件要求与上一平台实测记录
├── hardware/     # BOM、CAD、接线、参考资料与历史归档
├── reports/      # 系统与测试报告
├── scripts/      # 可复跑检查和测试工具
├── simulation/   # 仿真入口
├── src/          # ROS2 软件入口
└── presentation/ # 展示材料入口
```

## 历史资料

上一 STM32/JGB/WSDC 平台的 CAD、照片、接线和硬件台账保存在 `hardware/archive/`。历史文件中的完成状态仅对应其记录日期和当时平台；当前 H60 + MC520 新车以本 README、H60 架构文档和 H0-H8 验收计划为准。

## 版本、许可证与作者

- 当前开发版本：`v1.1-dev`；P2 完成并通过发布审查后进入 `v1.1`。
- 最新开发预发布：`v1.1-dev.1`（2026-08-20）；它冻结本轮仓库整改后的公开检查点，不表示 P2 已完成。
- 历史与未发布变化：[CHANGELOG.md](CHANGELOG.md)
- 许可证：当前 [LICENSE](LICENSE) 为待确定占位，复用或分发前请先确认后续正式许可。
- 作者：Yongzhe Xiong
