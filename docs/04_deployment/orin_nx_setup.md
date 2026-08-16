# Orin NX 环境搭建

> **当前补充**：Orin 环境继续沿用；原 Orin↔STM32 UART 结论不能直接迁移。新 Orin↔H60 链路需重新验证电平、协议和 H60 掉电时反供电。

## P1.4-0 Orin NX 实机基线记录

记录日期：2026-06-03

本节记录 P1.4 工程环境搭建开始前的 Orin NX 实机基线。后续安装 ROS2、传感器驱动、SLAM / Navigation 相关依赖前，应优先以本节作为环境起点。

### 1. 硬件与载板背景

| 项目 | 当前记录 |
| --- | --- |
| 计算模块 | Jetson Orin NX 16GB |
| 载板 / 套件 | Seeed reComputer Orin NX 16GB + J401 载板镜像 |
| 镜像标识 | `mfi_recomputer-orin-nx-16g-j401-6.2-36.4.3-2026-02-05.tar.gz` |
| 载板功耗边界 | 当前 J401 载板应保持在官方 25W 级运行边界内。JetPack 6.2 理论上可能暴露 Orin NX Super / 40W 能力，但本项目在当前非 Super 版 J401 载板上不启用 40W / MAXN SUPER。 |

### 2. 操作系统基线

| 项目 | 当前记录 |
| --- | --- |
| 主机名 | `project0-orin-nx` |
| 操作系统 | Ubuntu 22.04.5 LTS |
| 系统代号 | `jammy` |
| 架构 | `aarch64` / `arm64` |
| L4T 版本 | R36.4.3 |
| 内核版本 | `5.15.148-tegra` |
| `/etc/nv_tegra_release` 分支 | `R36.4.3` |

说明：当前 Seeed 镜像中，`dpkg-query --show nvidia-l4t-core` 未找到匹配的软件包。因此本文中的 L4T 版本从 `/etc/nv_tegra_release` 记录。

### 3. 资源基线

| 项目 | 当前记录 |
| --- | --- |
| 根分区磁盘 | 总计 457G，已用 20G，可用 418G，使用率 5% |
| 内存 | 总计 15Gi，基线检查时约使用 1.3Gi |
| Swap | 总计 7.6Gi |

### 4. 功耗模式基线

| 项目 | 当前记录 |
| --- | --- |
| 当前 `nvpmodel` 模式 | `25W` |
| `nvpmodel -q` 显示的模式 ID | `3` |
| 项目规则 | 除非后续载板 / 供电决策明确改变边界，否则当前 J401 载板上以 25W 作为最高运行模式。 |

### 5. 网络与远程访问基线

| 项目 | 当前记录 |
| --- | --- |
| 当前活动网络接口 | `wlp1p1s0` |
| 当前 IPv4 地址 | `<orin-nx-ip>/<prefix>` |
| SSH 服务 | `active (running)` |
| SSH 端口 | `22` |
| SSH 用户 | `<ssh-user>` |
| 远程访问命令 | `ssh user@<orin-nx-ip>` |

当前 IP 地址由 Wi-Fi 分配，后续可能变化。如果 SSH 连接失败，在 Orin NX 上用以下命令检查当前地址：

```bash
hostname -I
ip -br addr
```

### 6. ROS2 安装前已完成的本机可用性修复

开始 ROS2 安装前，已处理以下本机可用性问题：

1. Orin NX 启动问题定位为拆除外接按钮接线后残留的外部电源按钮 / 排针组件影响。
2. Firefox Snap 启动失败问题已通过重启 Snap 相关服务解决。
3. GNOME Terminal 启动失败问题定位为 locale 配置不完整；已将 `LANG` 恢复为 `zh_CN.UTF-8`。
4. 恢复过程中安装 / 使用了 `xterm` 作为备用终端。
5. 已确认浏览器和必要网络访问可用于后续开发资料查询。

### 7. 基线复查命令

在进行较大的环境变更前，可使用以下命令复查当前基线：

```bash
hostname
lsb_release -a
cat /etc/nv_tegra_release
uname -a
df -h
free -h
sudo nvpmodel -q
ip -br addr
systemctl status ssh --no-pager
locale
```

## P1.4 收束复查与网络排障记录

记录日期：2026-06-04

本节记录 P1.4 工程环境搭建收束复查前出现的一次 Orin NX 网络临时异常，以及恢复后的环境复查结果。该记录只用于部署与排障追溯，不表示网络问题永久闭环，也不表示 ROS2 / STM32 正式功能已经完成。

### 1. SSH 连接异常现象

Windows 侧连接 Orin NX 时出现：

```text
ssh <orin-nx-ip> 超时
ping <orin-nx-ip> 显示 Destination host unreachable
```

在 Orin NX 本机检查时，`ssh.service` 仍为 `active`。因此本次现象不判断为 SSH 服务损坏，而优先按网络链路异常处理。

### 2. Orin NX 本机排查线索

本机排查中观察到以下现象：

| 项目 | 当前记录 |
| --- | --- |
| SSH 服务 | `active` |
| Wi-Fi 状态 | `nmcli device status` 显示 Wi-Fi 断开 |
| Wi-Fi 扫描 | `nmcli device wifi list` 扫不到 Wi-Fi |
| Wi-Fi 发射功率线索 | `iw dev` 曾显示 `txpower -100.00 dBm` |
| rfkill 状态 | `Soft blocked: no` / `Hard blocked: no` |

当前解释：SSH 服务没有坏，主要异常在线路访问前的 Wi-Fi 模块 / 驱动状态。`rfkill` 未显示软 / 硬阻塞，因此本次不按用户主动禁用 Wi-Fi 处理。

### 3. 恢复结果

执行：

```bash
sudo reboot
```

重启后 Wi-Fi 恢复。恢复后的状态记录为：

| 项目 | 当前记录 |
| --- | --- |
| Wi-Fi 接口 | `wlP1p1s0` |
| 接口状态 | `UP` |
| IPv4 地址 | `<orin-nx-ip>/<prefix>` |
| Wi-Fi 连接 | `<wifi-ssid>` |
| 发射功率 | `txpower 7.00 dBm` |

结论：本次 Windows 侧 SSH 超时不是 SSH 服务损坏，而是 Orin NX Wi-Fi 模块 / 驱动临时异常；重启后网络恢复。后续如再次出现相同现象，应优先在 Orin NX 本机复查 `ip -br addr`、`nmcli device status`、`nmcli device wifi list`、`iw dev` 和 `rfkill`，再判断是否需要进一步处理无线网卡驱动或供电稳定性。

### 4. P1.4 环境收束复查结果

网络恢复后，用户按 P1.4 收束复查建议确认以下内容均正常：

1. Orin NX 可通过 SSH 继续访问；
2. Orin NX 当前 ROS2 Humble 环境变量可用；
3. `~/project0_ros2_ws` 工作区可继续执行 `colcon build`；
4. 最小测试包 `p0_bringup` 可被 ROS2 package 索引识别；
5. STM32 工具链、设备枚举、最小编译复验和 ST-LINK 通道边界记录维持当前已记录状态。

当前收束口径：

1. P1.4-0 Orin NX 实机基线已记录；
2. P1.4-1 ROS2 Humble 基础环境已完成最小通信验证；
3. P1.4-2 ROS2 工作区骨架已完成 `colcon build` 验证；
4. P1.4-3 STM32 工具链与设备识别已记录；
5. P1.4-4 STM32 最小工程编译链路已复验；
6. P1.4-5 STM32CubeProgrammer ST-LINK 通道边界已确认。

以上只表示工程环境搭建的最小验证链路已经可用，不表示 FAST-LIO2、Nav2、Livox 驱动、RealSense 驱动、正式 ROS2 功能包、正式 STM32 固件、STM32 烧录 / 调试、ROS2-STM32 通信、电机 / 电驱 / 主电池接线或 P2 装配验证已经完成。

## P1.4 远程开发与调试方案当前口径

记录日期：2026-06-04

当前 P1.4 最小收束中，远程访问已经确认到 SSH 可用：

```bash
ssh user@<orin-nx-ip>
```

该结果只表示 Orin NX 可按 headless + SSH 方式继续开发和排障，不表示完整远程调试方案已经冻结。VSCode Remote、远程桌面、文件同步、图形界面转发、串口调试协同和多终端工作流等内容，按真实开发需要在后续阶段再补充。

当前口径：

1. SSH 是已确认的最小远程访问方案；
2. 完整远程调试方案不作为 P2 前置条件；
3. 如果后续 P2-P6 实机开发中 SSH 不足以支撑调试，再补充远程开发记录。

## C1902 V1.1 载板 40W 综合压力测试

记录日期：2026-06-14

Orin NX 16GB 在 C1902 V1.1 载板上完成 20 分钟 CPU + GPU + 内存综合压力测试：

| 项目 | 结果 |
| --- | --- |
| 功耗模式 | `40W` / mode `4` |
| CPU / GPU 压力程序退出状态 | 均为 `0` |
| 最高 `tj / cpu` | `80.468C` |
| 最高 GPU 温度 | `76.25C` |
| 最高 `VDD_IN` | 约 `26.1W` |
| 过温停止阈值 | `85C`，未触发 |

测试期间未观察到重启、SSH 断连、进程异常退出或卡死。该结果只覆盖未接入相机、雷达和整车动力系统时的计算侧综合压力，不等同于真实业务负载或整车装车验收。

完整记录见 `../../reports/orin_nx_c1902_40w_mixed_stress_test_2026-06-14.md`。
