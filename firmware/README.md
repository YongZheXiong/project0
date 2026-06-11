# Firmware Workspace

本目录承接 Project0 STM32 固件相关记录、接口分配和后续正式固件源码。

当前已有记录：

| 文件 | 作用 | 状态 |
|---|---|---|
| `stm32_safe_init_v0_1.md` | 记录 P2 电驱控制端安全初始化工程、GPIO 分配、编译/调试路径和实测结果 | 已完成阶段记录 |
| `stm32_lf_single_motor_pulse_test_v0_1.md` | 记录左前 `LF` 单电机低占空比短脉冲测试的临时固件行为、诊断过程和测试结果 | 已完成阶段记录 |
| `stm32_four_single_motor_pulse_tests_v0_1.md` | 记录 `LF / LR / RF / RR` 四个单电机低占空比短脉冲测试、右侧实物映射、主输入保险故障处理和测试后安全回烧 | 已完成阶段记录 |
| `stm32_suspended_linkage_pulse_tests_v0_1.md` | 记录悬空同侧双电机联动、四轮联动、右侧方向补偿、`LF` 起转门槛诊断和测试后安全回烧 | 已完成阶段记录 |

当前注意：

1. STM32CubeIDE 测试工程保存在本地开发环境中，当前尚未纳入公开仓库源码管理；
2. 仓库内 `stm32_safe_init_v0_1.md` 只记录该工程的事实、关键代码行为和验证结果；
3. `stm32_lf_single_motor_pulse_test_v0_1.md` 只记录一次左前单电机临时测试；
4. `stm32_four_single_motor_pulse_tests_v0_1.md` 记录四个单电机测试均已通过；`stm32_suspended_linkage_pulse_tests_v0_1.md` 继续记录悬空同侧联动、四轮联动和方向补偿结果；
5. 当前右侧有效实物映射为 `RF = DRV-R M2 / PB9 / PD6 / PD7`，`RR = DRV-R M1 / PB8 / PD4 / PD5`；
6. 当前悬空方向一致性已通过，但仅在悬空、短时、人工看守条件下成立，不表示整车落地运动已完成；
7. 当前阶段测试结束后，STM32 已烧回安全初始化固件；
8. 正式底盘控制固件仍待后续建立，不应把安全初始化记录或临时测试记录等同于正式控制固件。
