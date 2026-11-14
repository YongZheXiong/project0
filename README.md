# Project0

Project0 是一台面向室内走廊的四轮差速移动机器人。项目以真机验证为主，目标依次覆盖底盘运动、定位建图、导航和最小语义任务。

## 当前进展

截至 2026-11-14，工程暂停在 P2。最新阶段性成果为 [v1.1.3 Nano 与 H60 架空控制基线](docs/releases/v1.1.3.md)。

| 项目 | 已有证据与当前状态 |
| --- | --- |
| 主计算与通信 | Jetson Orin Nano 8GB 接手上位机，Nano 通过 USB-COM 接 OpenCTR H60 V3.7。 |
| ROS 2 | Nano 上六包构建、接口生成、五节点运行与退出通过。17 段模式与安全仲裁场景使用软件替身消息。 |
| 四轮架空 | 真实手柄完成前后、左右方向、松使能停车、无线关机停车、显式恢复与持键重连无自启。 |
| 落地与结构 | 原 MC520P56 轮组已有短直行记录，轻左弧仍近直。新支架及霍尔编码器电机的装配与带载效果待验证。 |
| 感知 | D435 已取得有界 ROS 2 双流数据及非零深度样本。Mid360 已完成短窗接收与字段语义复核。传感器精度与整车导航集成仍待。 |
| 阶段验收 | P2 仍为 `v1.1-dev / Unreleased`。生产参数、里程计及完整落地运动验收尚未完成。 |

## 源码与文档

- [v1.1.3 完整发布说明](docs/releases/v1.1.3.md) · [架空验证报告](reports/nano_h60_raised_control_v1_1_3.md)
- [Nano、H60 与传感器连接基线](docs/02_architecture/p2_h60_rebuild_baseline.md) · [整车物料记录](hardware/bom.md) · [历史整车 CAD](hardware/cad/current_vehicle_v0_2/README.md)
- [ROS 2 源码及无设备验证](src/README.md) · [H60 固件构建与验证](firmware/h60_safe_control/README.md)
- [P2 H0–H8 验收计划](docs/06_testing/p2_h60_mc520_rebuild_acceptance_plan_2026-08-16.md) · [版本记录](CHANGELOG.md)

ROS 2 默认启动禁用电机指令，H60 默认构建保持 `MOTION=0 / CAL=0`。版本说明中的实测条件对应各自的配置。完整落地运动和实物安全以项目验收记录为依据。

## 历史版本

- [v1.1.2](docs/releases/v1.1.2.md) 冻结独立 H60 控制、架空前后运动与 USB-COM 断开停车。
- [v1.1.1](docs/releases/v1.1.1.md) 冻结四轮各自的运动方向、编码器符号、工程每圈计数与受限停车。
- [更早的发布说明](docs/releases/README.md)和 `hardware/archive/` 保留上一代底盘及开发快照。

作者为 Yongzhe Xiong。许可状态见 [LICENSE](LICENSE)。
