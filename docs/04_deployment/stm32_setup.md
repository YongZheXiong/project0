# STM32 开发环境搭建

> **历史记录**：本文仅描述上一平台。当前目标控制器是 H60 V3.7，部署入口见 [h60_setup.md](h60_setup.md)。

## P1.4-3 STM32 开发环境盘点与基础识别记录

记录日期：2026-06-03

本节记录 Windows 主机上 STM32 基础开发工具链与 USB 设备识别的初步盘点结果。当前阶段只确认工具链和设备枚举，不写正式固件、不烧录正式程序、不接电机、不接电驱、不接主电池，也不连接 Orin NX UART。

### 1. 当前目标边界

P1.4-3 当前只做以下事项：

1. 检查 Windows 上是否已有 STM32CubeIDE；
2. 检查 Windows 上是否已有 STM32CubeProgrammer；
3. 检查 Windows 是否能识别 STM32F407VET6 核心板 / 开发板 V5.5 相关 USB 设备；
4. 初步区分 CMSIS-DAP / USB Serial / COM 口 / ST-Link 类设备；
5. 记录工具链与设备识别状态。

当前不做以下事项：

1. 不创建正式 STM32 固件工程；
2. 不烧录正式程序；
3. 不接电机、电驱或主电池；
4. 不接 Orin NX UART；
5. 不把本节结果写成底盘控制、ROS2-STM32 通信或电气联调已完成。

### 2. STM32CubeIDE 检查结果

先检查常见默认路径：

```powershell
Test-Path "C:\ST\STM32CubeIDE"
```

本次输出：

```text
False
```

该结果只说明 `C:\ST\STM32CubeIDE` 这个常见路径不存在，不代表 STM32CubeIDE 一定没有安装。

随后检查 Windows 已安装程序登记项，确认：

| 项目 | 当前记录 |
| --- | --- |
| 软件 | STMicroelectronics STM32CubeIDE |
| 版本 | `1.19.0` |
| 安装路径 | 本地安装目录 |

结论：Windows 主机上已安装 STM32CubeIDE 1.19.0。

补充状态：用户确认 STM32CubeIDE 可以打开；更新过程中出现过信任来源 / 信任构件确认窗口，随后 CubeIDE 回到主界面，`Progress` 视图显示 `No operations to display at this time`。当前已确认 IDE 可启动并进入稳定主界面。

2026-06-04 补充：用户随后将 STM32CubeIDE 更新到 `2.1.1`，About 窗口显示：

| 项目 | 当前记录 |
| --- | --- |
| 软件 | STM32CubeIDE |
| 版本 | `2.1.1` |
| Build | `28236_20260312_0043 (UTC)` |

界面入口检查：用户确认 `File -> New` 菜单中存在 `STM32 Project` 入口。当前仅确认工程创建入口可见，尚未创建正式 STM32 工程。

2026-06-04 补充：STM32CubeIDE 更新到 `2.1.1` 后，新建工程入口行为与 `1.19.0` 有变化。为避免误选 CMake / Empty Project 路径，本次升级后复验改用独立 STM32CubeMX 生成 STM32CubeIDE 工程，再导入 STM32CubeIDE 编译。

### 3. STM32CubeProgrammer 检查结果

先检查常见默认路径：

```powershell
Test-Path "C:\Program Files\STMicroelectronics\STM32Cube\STM32CubeProgrammer"
```

本次输出：

```text
False
```

初次检查时，在 Windows 已安装程序登记项中按 `STM32CubeProgrammer` / `CubeProgrammer` 关键字查询，未发现匹配项。

随后从 STMicroelectronics 官方渠道下载并安装 Windows 64 位安装器：

```text
SetupSTM32CubeProgrammer_win64.exe
```

安装后在 Windows 已安装程序登记项中确认：

| 项目 | 当前记录 |
| --- | --- |
| 软件 | STM32CubeProgrammer |
| 版本 | `2.22.0` |

用户确认 STM32CubeProgrammer 可正常打开。

结论：Windows 主机上已安装 STM32CubeProgrammer 2.22.0，并已确认可启动。当前仅确认工具链可用，不连接目标板、不擦除、不下载、不烧录正式程序。

### 4. STMicroelectronics 驱动登记项

Windows 已安装程序登记项中发现以下 STMicroelectronics 驱动包：

| 项目 | 当前记录 |
| --- | --- |
| STLink WinUSB 驱动包 | `Windows Driver Package - STMicroelectronics (WinUSB) STLinkWinUSB (06/08/2017 2.01)` |
| ST usbser 驱动包 | `Windows Driver Package - STMicroelectronics (usbser) Ports (06/08/2017 2.01)` |

结论：Windows 主机上已有 STMicroelectronics 相关 WinUSB 与 usbser 驱动包登记记录。

### 5. Windows 设备识别检查结果

原计划使用：

```powershell
Get-PnpDevice | Where-Object { $_.FriendlyName -match "STM|ST-Link|STLink|CMSIS|DAP|USB Serial|COM" } | Format-Table -AutoSize
```

但在当前终端会话中该命令返回：

```text
Get-PnpDevice : 拒绝访问
```

这表示当前会话无权通过该接口读取 PnP 设备列表，不表示 STM32 开发板、CMSIS-DAP、ST-Link 或串口设备损坏。

随后使用 `pnputil` 读取设备枚举，发现以下相关条目：

| 设备线索 | 当前记录 |
| --- | --- |
| CMSIS-DAP 相关 USB 设备 | `USB\VID_0416&PID_5051\CMSIS-DAP` |
| 设备描述 | `USB Composite Device` |
| 当前状态 | `Started` |
| 驱动 | `usb.inf` |

串口类设备中发现以下与 USB 串口相关的条目：

| 设备线索 | 当前记录 |
| --- | --- |
| USB 串行设备 | `USB\VID_0416&PID_5051&MI_01\6&1929203c&0&0001` |
| 设备描述 | `USB 串行设备 (COM8)` |
| 当前状态 | `Started` |
| 驱动 | `usbser.inf` |

同时系统中还存在多个蓝牙 RFCOMM 串口，例如 `COM3`、`COM4`、`COM5`、`COM7`、`COM10`、`COM11`。这些是蓝牙链接上的标准串行端口，不应直接当作 STM32 开发板 USB 转串口来使用。

当前解释：

1. Windows 曾经枚举到 VID/PID 为 `0416:5051` 的 CMSIS-DAP / USB 串口复合设备；
2. 复查时 CMSIS-DAP 复合 USB 设备状态为 `Started`，说明 Windows 当前已识别到板载 CMSIS-DAP 设备；
3. 复查时 USB 串行设备状态为 `Started`，并枚举为 `COM8`；
4. 当前可以确认 USB 线具备数据传输能力，开发板的 CMSIS-DAP 与 USB 串口枚举基础可用。

### 6. 建议复查命令与解读

插入 STM32F407VET6 核心板 / 开发板 V5.5 后，建议先只复查设备识别，不打开烧录流程。

```powershell
pnputil /enum-devices /instanceid "USB\VID_0416&PID_5051\CMSIS-DAP"
```

这条命令做什么：查看 Windows 记录的 CMSIS-DAP 复合 USB 设备详情。

为什么现在运行：确认开发板板载调试器是否被 Windows 识别为当前连接设备。

正常输出怎么看：如果 `Status` 显示 `Started`，通常表示设备当前已连接并由 Windows 驱动接管。

异常输出怎么看：如果 `Status` 仍是 `Disconnected`，说明 Windows 当前没有把它识别为正在连接；如果找不到实例，说明设备枚举记录不存在或 VID/PID 不匹配。

```powershell
pnputil /enum-devices /class Ports
```

这条命令做什么：列出 Windows 当前登记的串口类设备。

为什么现在运行：确认开发板的 USB 转串口是否枚举为 `COMx`。

正常输出怎么看：应重点寻找非蓝牙的 `USB 串行设备 (COMx)`，并查看它的 `Status` 是否为 `Started`。

异常输出怎么看：如果只看到蓝牙串口，或者 USB 串行设备为 `Disconnected`，说明当前还没有确认开发板串口在线。

### 7. 当前结论

P1.4-3 已完成初步工具链与设备识别盘点：

1. STM32CubeIDE 已确认安装，版本为 `1.19.0`；
2. STM32CubeIDE 已确认可启动并进入稳定主界面；
3. `File -> New` 菜单中已确认存在 `STM32 Project` 入口，但尚未创建正式工程；
4. STM32CubeProgrammer 已确认安装，版本为 `2.22.0`，并可正常打开；
5. Windows 已有 STMicroelectronics WinUSB / usbser 驱动包登记记录；
6. Windows 已确认识别到 CMSIS-DAP 复合 USB 设备，状态为 `Started`；
7. Windows 已确认识别到 USB 串行设备 `COM8`，状态为 `Started`；
8. 当前阶段仍停留在工具链与设备识别，不进入正式固件、烧录、接线或电气联调。

## P1.4-4 STM32 最小工程创建与编译验证记录

记录日期：2026-06-03

本节记录 STM32CubeIDE 中基于 STM32F407VET6 的最小工程创建、代码生成和编译验证结果。当前阶段只验证 IDE、固件库包和编译工具链可用，不烧录程序、不连接目标板、不执行调试、不接电机、电驱、主电池或 Orin NX UART。

### 1. 工程创建目标

本次最小工程用于验证：

1. STM32CubeIDE 可选择 `STM32F407VET6` 目标芯片；
2. STM32Cube F4 固件库包可被 CubeIDE 识别；
3. CubeIDE 可生成基础 STM32Cube 工程；
4. ARM GCC 工具链可完成最小工程编译；
5. 生成结果只作为工具链验证，不作为正式底盘控制固件。

### 2. 固件库包补齐过程

首次创建 STM32Cube 工程时，CubeIDE 提示缺少必要 firmware package，无法完成工程创建：

```text
Code generation could not be done most probably because the necessary firmware package is missing.
Not able to complete STM32Cube project creation.
```

CubeIDE 在线登录 / 下载过程中出现过网络连接失败和 `api_config.json (Not available)` 提示。因此本次改用 STMicroelectronics 官方下载的本地压缩包导入 STM32Cube F4 固件库。

已下载并使用以下本地包：

| 文件 | 作用 |
| --- | --- |
| `<Windows 用户目录>\\Downloads\stm32cubef4-v1-28-0.zip` | STM32CubeF4 主包 |
| `<Windows 用户目录>\\Downloads\stm32cubef4-v1-28-3.zip` | STM32CubeF4 补丁包 |

导入补丁包时，CubeIDE 曾提示缺少：

```text
stm32cube_fw_f4_v1280.zip
```

处理方式：将已下载的 `stm32cubef4-v1-28-0.zip` 复制到 CubeIDE Repository，并命名为补丁导入器要求的文件名：

```powershell
Copy-Item -LiteralPath "<Windows 用户目录>\\Downloads\stm32cubef4-v1-28-0.zip" -Destination "<STM32Cube Repository>\stm32cube_fw_f4_v1280.zip"
```

随后确认 Repository 中存在：

```text
<STM32Cube Repository>\STM32Cube_FW_F4_V1.28.0
<STM32Cube Repository>\STM32Cube_FW_F4_V1.28.3
```

### 3. 首次工程创建异常

首次尝试创建工程时，工程名疑似前置空格导致生成了异常本地临时工程目录。

该目录中生成了部分 `Core`、`Drivers` 和 `main.c`，但缺少 CubeIDE C/C++ 工程识别所需的 `.cproject`，导致 `Build Project` 不可用。该目录只作为异常过程记录，不作为本次验证通过工程。

另有不带前置空格的残留目录，内容不完整，仅作为失败残留记录，不作为本次验证通过工程。

### 4. 最小工程编译验证结果

随后用户重新创建了一个干净的最小工程。当前通过编译验证的工程目录为本地临时工程目录。

该工程目录中已确认存在：

1. `.project`
2. `.cproject`
3. `.mxproject`
4. `1.ioc`
5. `Core/`
6. `Drivers/`
7. `Debug/`
8. `STM32F407VETX_FLASH.ld`
9. `STM32F407VETX_RAM.ld`

CubeIDE Console 中显示已调用 ARM GCC 工具链，例如：

```text
arm-none-eabi-gcc
arm-none-eabi-size 1.elf
arm-none-eabi-objdump -h -S 1.elf > "1.list"
```

编译结果：

```text
Build Finished. 0 errors, 0 warnings.
```

构建耗时记录：

```text
took 44s.398ms
```

生成的目标文件名：

```text
1.elf
```

### 5. 当前结论

P1.4-4 STM32 最小工程创建与编译验证已完成：

1. STM32Cube F4 固件库已补齐到 `V1.28.3`；
2. STM32CubeIDE 可创建 STM32F407VETx 最小工程；
3. 本地临时工程已完成编译；
4. 编译结果为 `0 errors, 0 warnings`；
5. 当前验证只证明 STM32CubeIDE、STM32Cube F4 固件库和 ARM GCC 编译链路可用；
6. 当前未烧录程序、未连接目标板、未调试运行、未接电机、电驱、主电池或 Orin NX UART；
7. 该工程只是最小编译验证工程，不是项目0正式 STM32 固件工程。

### 6. STM32CubeIDE 2.1.1 升级后复验

记录日期：2026-06-04

用户将 STM32CubeIDE 更新到 `2.1.1` 后，使用独立 STM32CubeMX `6.17.0` 重新生成最小 STM32F407VETx 工程，并导入 STM32CubeIDE 进行编译复验。

本次复验工具链记录：

| 项目 | 当前记录 |
| --- | --- |
| STM32CubeIDE | `2.1.1` |
| STM32CubeIDE Build | `28236_20260312_0043 (UTC)` |
| STM32CubeMX | `6.17.0` |
| 固件库 | `STM32Cube FW_F4 V1.28.3` |
| 目标芯片 | `STM32F407VETx` |
| 工程语言 | `C` |
| Toolchain / IDE | `STM32CubeIDE` |

CubeMX 代码生成结果：

```text
The Code is successfully generated under:
<local STM32 workspace>/p14_4_f407_build_check_v2
```

随后在 STM32CubeIDE 中通过 `File -> Open Projects from File System...` 导入该工程。当前通过升级后复验的工程目录为本地临时工程目录。

该目录中已确认存在：

1. `.project`
2. `.cproject`
3. `.mxproject`
4. `p14_4_f407_build_check_v2.ioc`
5. `Core/`
6. `Drivers/`
7. `STM32F407VETX_FLASH.ld`
8. `STM32F407VETX_RAM.ld`

STM32CubeIDE Console 编译记录显示：

```text
Build of configuration Debug for project p14_4_f407_build_check_v2
make -j24 all
Finished building target: p14_4_f407_build_check_v2.elf
```

生成目标文件：

```text
p14_4_f407_build_check_v2.elf
```

编译尺寸记录：

```text
text    data    bss     dec     hex     filename
4728    12      1572    6312    18a8    p14_4_f407_build_check_v2.elf
```

编译结果：

```text
Build Finished. 0 errors, 0 warnings. (took 41s.23ms)
```

复验结论：

1. STM32CubeIDE 已更新到 `2.1.1`，并可导入 CubeMX 生成的 STM32CubeIDE 工程；
2. STM32CubeMX `6.17.0` 可为 `STM32F407VETx` 生成最小工程；
3. STM32Cube F4 固件库 `V1.28.3` 可被 CubeMX / CubeIDE 使用；
4. 本地临时工程已在 STM32CubeIDE `2.1.1` 中完成编译；
5. 编译结果为 `0 errors, 0 warnings`；
6. 本次复验只证明 STM32 工具链、固件库和最小工程编译链路可用；
7. 当前仍未烧录程序、未连接目标板、未调试运行、未接电机、电驱、主电池或 Orin NX UART；
8. 该工程只是最小编译复验工程，不是项目0正式 STM32 固件工程。

## P1.4-5 STM32 下载 / 调试接口边界确认记录

记录日期：2026-06-04

本节记录 STM32CubeProgrammer 对当前 STM32F407VET6 核心板 / 开发板 V5.5 的 ST-LINK 通道识别结果。当前阶段只确认下载 / 调试工具边界，不擦除、不下载、不烧录、不调试运行、不接电机、电驱、主电池或 Orin NX UART。

### 1. 当前目标边界

P1.4-5 当前只做以下事项：

1. 打开 STM32CubeProgrammer；
2. 选择 `ST-LINK` 连接方式；
3. 刷新 ST-LINK 设备列表；
4. 记录 CubeProgrammer 是否能发现 ST-LINK 类调试器；
5. 将该结果与 Windows 侧 CMSIS-DAP / USB Serial 识别结果区分记录。

当前不做以下事项：

1. 不点击 `Connect` 尝试连接目标芯片；
2. 不点击 `Erase`；
3. 不点击 `Download`；
4. 不写入 Flash；
5. 不执行调试运行；
6. 不把本节结果写成 STM32 已可下载、已烧录、已运行或已完成底盘控制联调。

### 2. STM32CubeProgrammer ST-LINK 通道检查结果

检查工具：

| 项目 | 当前记录 |
| --- | --- |
| 软件 | STM32CubeProgrammer |
| API 版本 | `v2.22.0` |
| 平台 | `Windows-64Bits` |

用户在 STM32CubeProgrammer 中选择 `ST-LINK` 连接方式并刷新设备列表后，界面显示：

| 项目 | 当前记录 |
| --- | --- |
| 连接方式 | `ST-LINK` |
| Serial number | `No ST-LINK...` |
| 状态 | `Not connected` |
| Port | `SWD` |
| Target information | 未显示目标板 / Device / CPU 信息 |

### 3. 当前解释

该结果与 P1.4-3 中 Windows 设备枚举记录一致：

1. Windows 侧已识别当前板载 USB 复合设备为 CMSIS-DAP / USB Serial 相关设备；
2. STM32CubeProgrammer 的 `ST-LINK` 通道未发现 ST-LINK 类调试器；
3. 当前现象不等于 STM32 开发板损坏，也不等于 USB 线不可用；
4. 当前只能确认：这块板在现有 USB 连接下，不表现为 STM32CubeProgrammer 可直接识别的 ST-LINK 设备；
5. 后续如需下载 / 调试，应在对应阶段再确认可行路径，例如外接 ST-LINK，或评估 CMSIS-DAP / OpenOCD 等路径；当前不提前展开正式下载 / 调试流程。

### 4. 当前结论

P1.4-5 STM32 下载 / 调试接口边界确认已完成：

1. STM32CubeProgrammer `2.22.0` 可正常打开；
2. `ST-LINK` 连接方式下未发现 ST-LINK 设备，界面显示 `No ST-LINK...`；
3. 当前结果与 Windows 侧 CMSIS-DAP / USB Serial 枚举结果一致；
4. 当前未连接目标芯片、未擦除、未下载、未烧录、未调试运行；
5. 当前不把 STM32CubeProgrammer 的 ST-LINK 通道写成已可用下载链路；
6. 当前也不把 `No ST-LINK...` 写成板子故障，只记录为工具链边界。

## P2 CMSIS-DAP / OpenOCD 与控制板故障状态

记录日期：2026-06-17

后续 P2 实测已确认 WCH-Link / CMSIS-DAP 可由 OpenOCD 识别，因此下载 / 调试路径不再只依赖 STM32CubeProgrammer 的 ST-LINK 通道。

但原 STM32 控制板随后出现板载 3.3V 供电故障：

1. 5V 输入正常；
2. 3.3V 仅为零点几伏；
3. `RESET / NRST = 0V`；
4. 外接控制线拔除后未发现 5V / 3.3V 对地硬短路；
5. 当前不能继续 SWD 目标连接、USART3 烧录或动力测试。

替换板需要按单板供电、车载 5V、SWD、USART3 和 Orin NX 收包的顺序重新验收。技术摘要见 `../../hardware/wiring/p2_stm32_power_fault_summary_2026-06-17.md`。

## P2 替换板、UART、编码器与工程迁移状态

记录日期：2026-07-13

后续 P2 实测已完成以下闭环：

1. 替换 STM32 控制板完成基础供电、CMSIS-DAP / OpenOCD 和目标芯片识别；
2. USART3 三线通信链路恢复，Orin NX 可读取 STM32 周期输出；
3. STM32 可周期输出 `P0_STM32_UART_OK` 和四路编码器计数摘要；
4. Orin NX 向 STM32 发送测试文本后，STM32 可回传 ACK；
5. 四路编码器在第 4 路动力保险空置、人工手动转轮、UART 读数条件下均已产生有效计数；
6. 左前 `LF` 替换电机并重新压紧编码器供电 / 地线后，低功率手动转轮复验通过；
7. 旧开发主机上的当前项目 STM32 工程已迁移到新开发主机，并完成构建检查；
8. 车上 STM32 flash 已完成只读备份，active 固件前缀与迁移工程产物和新开发主机构建产物一致。

当前公开边界：

1. 该结果说明 STM32 工程恢复、构建和备份路径成立；
2. 该结果不表示正式底盘控制协议、通信中断停车、无新指令停车、编码器方向符号归一化或里程计已经完成；
3. 该结果不开放主动动力、悬空动力或落地低速运动；
4. 后续若需要烧录，仍需重新确认目标固件、flash 备份、供电状态、第 4 路动力保险状态、急停和回滚方案。
