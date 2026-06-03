# Orin NX 环境搭建

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
| 主机名 | `gdsdc-desktop` |
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
| 当前 IPv4 地址 | `10.40.146.23/21` |
| SSH 服务 | `active (running)` |
| SSH 端口 | `22` |
| SSH 用户 | `gdsdc` |
| 远程访问命令 | `ssh gdsdc@10.40.146.23` |

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
5. 已安装并配置 Clash Verge ARM64 包；Firefox 可通过 Clash 访问 ChatGPT。

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


