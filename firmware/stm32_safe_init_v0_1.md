# STM32 安全初始化固件记录 v0.1

## 1. 文件作用

本文档记录 Project0 P2 装配阶段用于电驱控制端安全默认状态验证的 STM32 最小安全初始化固件工程、GPIO 分配、编译/调试路径和实测结果。

本文档不是正式底盘控制固件设计，不包含闭环控制、编码器读取、UART 通信、ADC 采样或 ROS2 通信协议。

## 2. 工程位置

本记录对应的 STM32CubeIDE 测试工程保存在本地开发环境中。当前公开仓库只记录该工程的事实和验证结果，尚未把该 STM32CubeIDE 工程源码纳入公开仓库源码管理。

## 3. 目标

该最小固件只做一件事：

```text
STM32 上电后立即把两块电驱置于安全脱机状态。
```

根据 WSDC2412D-V3.0 数据手册，`INA=H, INB=H` 为脱机，输入悬空时默认为高电平。因此当前安全默认状态为：

```text
PWM = 0
INA = 1
INB = 1
电驱状态 = 脱机
```

## 4. GPIO 分配

说明：下表中的 `RF_*` / `RR_*` 名称沿用当前 STM32CubeIDE 工程早期生成标签；2026-06-11 四电机单电机测试后，右侧实物电机映射已调整为 `RF = PB9 / PD6 / PD7`、`RR = PB8 / PD4 / PD5`。安全初始化对所有 PWM 和 INA / INB 同时置为安全态，因此不受右侧逻辑命名交换影响；正式底盘控制固件必须按当前实物映射实现。

| 信号 | STM32 引脚 | 默认状态 |
|---|---|---|
| `LF_PWM` | `PB6` | Low |
| `LR_PWM` | `PB7` | Low |
| `RR_PWM` / 工程旧标签 `RF_PWM` | `PB8` | Low |
| `RF_PWM` / 工程旧标签 `RR_PWM` | `PB9` | Low |
| `LF_INA` | `PD0` | High |
| `LF_INB` | `PD1` | High |
| `LR_INA` | `PD2` | High |
| `LR_INB` | `PD3` | High |
| `RR_INA` / 工程旧标签 `RF_INA` | `PD4` | High |
| `RR_INB` / 工程旧标签 `RF_INB` | `PD5` | High |
| `RF_INA` / 工程旧标签 `RR_INA` | `PD6` | High |
| `RF_INB` / 工程旧标签 `RR_INB` | `PD7` | High |

CubeMX GPIO 参数：

| 项目 | 设置 |
|---|---|
| GPIO mode | `Output Push Pull` |
| Pull-up/Pull-down | `No pull-up and no pull-down` |
| GPIO speed | Low |
| SYS Debug | Serial Wire |

## 5. 生成代码关键逻辑

`Core/Src/gpio.c` 中生成逻辑已检查，关键行为如下：

```c
HAL_GPIO_WritePin(GPIOD, LF_INA_Pin|LF_INB_Pin|LR_INA_Pin|LR_INB_Pin
                        |RF_INA_Pin|RF_INB_Pin|RR_INA_Pin|RR_INB_Pin,
                        GPIO_PIN_SET);

HAL_GPIO_WritePin(GPIOB, LF_PWM_Pin|LR_PWM_Pin|RF_PWM_Pin|RR_PWM_Pin,
                  GPIO_PIN_RESET);
```

`main.c` 中已调用：

```c
MX_GPIO_Init();
```

## 6. 编译结果

工程 `project0_stm32_safe_init` 编译通过：

```text
Build Finished. 0 errors, 0 warnings.
```

生成目标文件为 `project0_stm32_safe_init.elf`。

## 7. 下载 / 调试路径

当前 STM32F407VET6 核心板在 Windows 侧表现为 CMSIS-DAP / USB Serial 设备，不是 ST-LINK 设备。

CubeIDE 内部调试配置要点：

| 项目 | 当前口径 |
|---|---|
| 调试方式 | OpenOCD |
| 调试器脚本 | 测试配置指定 `project0_stm32_safe_init.cfg` |
| OpenOCD interface | `interface/cmsis-dap.cfg` |
| transport | `swd` |
| 备注 | CubeIDE 界面标签可能仍显示 `ST-LINK (OpenOCD)`，但实际脚本应为 CMSIS-DAP |

关键 OpenOCD 连接结果：

```text
Info : accepting 'gdb' connection on tcp/3333
[STM32F407VETx.cpu] halted due to breakpoint
Info : device id = 0x101f6413
Info : flash size = 512 KiB
```

说明：已能通过 OpenOCD 连接 STM32F407VETx、识别 Flash，并进入 Debug 运行。

## 8. 实测验证

验证条件：

1. 主电池未接；
2. 电驱动力端 `P+ / P-` 未接；
3. 两块电驱控制端 `VCC` 已接 STM32 `3.3V`；
4. 两块电驱控制端 `GND` 已接 STM32 `GND`；
5. 程序处于运行状态。

验证结果：

| 测点 | 目标 | 结果 |
|---|---|---|
| 两块电驱 `VCC` | 约 `3.3V` | 符合 |
| 两块电驱 `GND` | `0V` | 符合 |
| 两块电驱 `PWM1 / PWM2` | 约 `0V` | 符合 |
| 两块电驱 `INA / INB` | 约 `3.3V` | 符合 |

结论：

```text
STM32 安全初始化固件已烧录并运行成功。
两块电驱在控制端接入情况下保持 PWM=0、INA=H、INB=H，即脱机状态。
```

## 9. 当前停点

当前已停止在控制端验证完成阶段：

1. Debug 会话已关闭；
2. 主电池仍未接；
3. 电驱动力端 `P+ / P-` 仍未接；
4. 未进行电机动力测试；
5. 下一步应进行低风险单电机动力测试准备。

## 10. 后续要求

正式底盘控制固件应继承以下原则：

1. 上电后首先进入安全状态；
2. PWM 默认 `0%`；
3. 默认方向状态采用 `INA=H, INB=H` 脱机；
4. 正反转切换前先将 PWM 降至 `0%`；
5. 未完成急停链路前，不进行无人看守或落地动力测试；
6. 后续加入 TIM4 PWM 输出时，仍必须保证启动默认占空比为 `0%`；
7. 后续正式固件必须采用当前右侧实物映射：`RF = PB9 / PD6 / PD7`，`RR = PB8 / PD4 / PD5`。
