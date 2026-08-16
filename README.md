# Project0

Project0 是一个面向室内走廊环境的具身智能四轮差速小车项目，目标是建立可验证、可维护的感知—决策—执行闭环，并把安全约束作为系统能力的一部分。

## 当前状态

截至 2026-08-16，项目已批准 **OpenCTR H60 V3.7 + 4 × MC520P56_12V + 65 mm 橡胶轮** 的重建数字基线。此前 STM32 + WSDC2412D + JGB37-520 + 三层底盘属于上一版实车，相关记录仅用于历史追溯，不能作为新车上电或运动准入依据。

| 项目 | 当前口径 |
| --- | --- |
| 阶段 | P2 重建：设计基线已统一，等待到货确认、新 CAD、线束定额、固件和 H0-H8 验收 |
| 主计算 | Jetson Orin NX 16GB |
| 底层控制 | OpenCTR H60 V3.7，四路本地电驱与编码器闭环 |
| 轮系 | 4 × MC520P56_12V，1:56，配套支架/线束/联轴器，65 mm 橡胶轮 |
| 感知 | Livox Mid360 + Intel RealSense D435 |
| 电源 | 3S 电池经 25A 主保险、主开关和带支路保护的分配端，分别供 H60、Orin、Mid360 |
| 急停 | NC 控制继电器，仅切断 H60 正极；NO 作为 Orin 3.3V GPIO 干接点反馈 |
| 采样 | H60 PC0 监测 VIN；首版不安装 Keyes 分压板或 ACS712 |

这只是数字工程基线，不表示套件已经到货、整车已经接线、上电或具备落地运动条件。

## 关键安全边界

- H60、Orin 和 Mid360 使用独立支路；Orin 与 Mid360 不从 H60 供电。
- 急停按下后 H60 和电机失电，Orin 与 Mid360 保持运行；急停复位后仍必须经过新的显式 ARM 才能运动。
- H60 必须在上电、复位、通信超时和异常后保持 `DISARMED/PWM=0`。
- Orin 保活而 H60 失电会带来 UART 反供电风险，正式线束必须先完成测量并采用掉电高阻的缓冲或隔离方案。
- H60 的 TVS、驱动过流保护和 VIN ADC 都不能替代主保险、支路保险、急停或实测验收。
- H60 失电后 VIN 遥测也会消失；首版不具备急停后的独立电池电压/电流遥测。

## 主要入口

- [当前实现基线](docs/02_architecture/p2_h60_rebuild_baseline.md)
- [H60 电源与急停接线](hardware/wiring/h60_power_estop_wiring_v0_1.md)
- [H60 安全固件要求](firmware/h60_safety_firmware_requirements_v0_1.md)
- [H0-H8 重建验收计划](docs/06_testing/p2_h60_mc520_rebuild_acceptance_plan_2026-08-16.md)
- [当前公开 BOM](hardware/bom.md)
- [重建与仓库统一报告](reports/h60_mc520_rebuild_baseline_2026-08-16.md)

## 目录

```text
Project0/
├── docs/                 # 规划、架构、部署与测试
├── firmware/             # 当前固件要求及历史 STM32 记录
├── hardware/             # BOM、接线和 CAD 资料
├── reports/              # 公开测试与审查报告
├── scripts/              # 可复跑工具
├── src/                  # ROS2 源码入口
└── README.md
```

## 后续顺序

到货与版本确认 → 新 CAD 与质量/重心检查 → 断电接线检查 → 独立低功率上电 → 急停和反供电验证 → 安全固件 → 单路/四路悬空动力 → 落地低速。
