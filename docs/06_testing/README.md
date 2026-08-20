# 测试与验收文档索引

## 1. 目录职责

`docs/06_testing/` 用于承载 Project0 的测试计划、验收清单、阶段门判定和测试结果索引。

本目录不替代：

1. 项目内部的 WBS、风险和事前规划；
2. `hardware/`、`firmware/`、`docs/04_deployment/` 中的原始实施与测试记录；
3. 内部变更执行记录；
4. 内部日常过程记录；
5. `reports/` 中面向总结和展示的正式报告。

## 2. 当前文件

| 文件 | 状态 | 职责 |
| --- | --- | --- |
| `p2_h60_mc520_rebuild_acceptance_plan_2026-08-16.md` | 当前执行入口 / H1 实物复核中，其余实物项 NOT RUN | H60 + MC520 新车 H0-H8 到货、CAD、三支路电气、固件、动力瞬态和落地准入 |
| `current_vehicle_h1_cad_review_2026-08-18.md` | 两轮数字审查完成 / H1 IN REVIEW | 保留第一轮问题并追加 2026-08-19 修正版 STEP 的拓扑、轴距/轮距、离地间隙、支柱、传感器姿态和加工状态复审 |

## 3. 当前 H60 与历史 STM32 记录

当前 H60 固件要求见 [`firmware/h60_motion_control_firmware_requirements_v0_2.md`](../../firmware/h60_motion_control_firmware_requirements_v0_2.md)。

以下记录包含上一 STM32 平台的临时固件行为、GPIO / 通道映射、工程与烧录信息、安全边界、诊断过程和测试结果，因此只读保留：

| 文件 | 内容 |
| --- | --- |
| [`firmware/stm32_safe_init_v0_1.md`](../../firmware/stm32_safe_init_v0_1.md) | 电驱控制端安全初始化固件与实测验证 |
| [`firmware/stm32_lf_single_motor_pulse_test_v0_1.md`](../../firmware/stm32_lf_single_motor_pulse_test_v0_1.md) | 左前单电机短脉冲测试 |
| [`firmware/stm32_four_single_motor_pulse_tests_v0_1.md`](../../firmware/stm32_four_single_motor_pulse_tests_v0_1.md) | 四个单电机短脉冲测试与通道映射 |
| [`firmware/stm32_suspended_linkage_pulse_tests_v0_1.md`](../../firmware/stm32_suspended_linkage_pulse_tests_v0_1.md) | 悬空同侧及四轮联动测试 |
| [`firmware/stm32_uart3_minimal_test_v0_1.md`](../../firmware/stm32_uart3_minimal_test_v0_1.md) | USART3 最小测试固件、双向 ACK 与重启 / 冷启动复验 |
| [`firmware/stm32_encoder_acceptance_v0_1.md`](../../firmware/stm32_encoder_acceptance_v0_1.md) | 旧平台新映射安全输出、四路编码器手动转轮和 `LF` 交叉故障定位 |

这些既有动力测试仅用于历史追溯，不能直接作为 H60 新平台接线或固件依据。

## 4. 使用规则

1. 阶段门记录形成后作为历史判定依据保留；如需纠正，应新增更正说明，不静默改写历史。
2. 执行中验收清单只把已经真实验证的事项写成完成。
3. 详细原始结果仍写入对应硬件、固件、部署或测试记录，验收清单只汇总判定和准入状态。
4. 后续新增阶段验收文件时，应区分“验收标准 / 执行清单 / 结果记录 / 阶段门记录”，避免一个文件同时承担全部职责。
