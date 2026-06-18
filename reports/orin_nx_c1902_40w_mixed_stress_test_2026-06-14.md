# Orin NX C1902 V1.1 40W 综合压力测试记录

## 1. 记录目的

本文记录 C1902 V1.1 载板更换后，Orin NX 16GB 在 `40W` 模式下进行 CPU + GPU + 内存综合压力测试的结果。

本次测试用于补充 C1902 载板的 `40W / MAXN SUPER` 稳定性验证，但只覆盖未接入相机、雷达、整车动力和真实 ROS2 业务负载时的计算侧压力测试，不替代后续装车联调、真实模型推理、传感器采集或长期运行验收。

## 2. 测试环境

| 项目 | 记录 |
| --- | --- |
| 测试日期 | 2026-06-14 |
| 主机名 | 已脱敏 |
| SSH 地址 | 已脱敏 |
| 计算模块 | Jetson Orin NX 16GB |
| 载板 | C1902 V1.1 Orin Nano / NX 系列载板 |
| 系统 | Ubuntu 22.04 / Jetson Linux R36.4 系列环境 |
| 内核 | `5.15.148-tegra` |
| 当前功耗模式 | `NV Power Mode: 40W` / mode `4` |
| 测试工具 | `stress-ng`、`nvcc`、CUDA 自定义 GPU 压力程序、`tegrastats` |
| 外设接入状态 | 相机、雷达、整车动力系统未接入 |
| 远程执行方式 | 通过同一局域网内的 SSH 远程执行 |

说明：本次远程测试时 `sudo` 仍需密码，因此未在脚本中重新执行 `sudo jetson_clocks`。测试开始时 `nvpmodel -q` 已确认设备处于 `40W` 模式。

## 3. 测试负载

综合负载由两部分同时运行：

1. CPU / 内存 / 矩阵压力：

```bash
stress-ng --cpu 4 --cpu-method matrixprod --vm 2 --vm-bytes 2G --matrix 2 --timeout 1200s --metrics-brief
```

2. CUDA GPU 压力程序：

```bash
./gpu_stress 1200
```

温度、频率和功耗记录：

```bash
tegrastats --interval 1000 --logfile tegrastats.log
```

脚本带有 `tj >= 85C` 自动停止保护。

## 4. 预检结果

先执行 3 分钟预检，结果如下：

| 指标 | 结果 |
| --- | --- |
| CPU 负载 | 8 核满载 |
| GPU 负载 | `GR3D_FREQ` 最高约 `99%` |
| 最高 `tj / cpu` | `77.5C` |
| 最高 GPU 温度 | `73.312C` |
| 最高输入功耗 | `25904mW`，约 `25.9W` |
| 结论 | 通过，可继续正式测试 |

## 5. 20 分钟正式测试结果

正式测试持续 20 分钟，结果如下：

| 指标 | 结果 |
| --- | --- |
| 测试目录 | `~/orionx_thermal_test/mixed_<timestamp>` |
| 持续时间 | `1200s` |
| CPU 压力程序退出状态 | `0` |
| GPU 压力程序退出状态 | `0` |
| CPU 负载 | 测试期间 8 核持续接近或达到满载 |
| GPU 负载 | 测试期间 `GR3D_FREQ` 基本维持 `99%`，结束阶段降为 `0%` |
| 最高 `tj / cpu` | `80.468C` |
| 最高 GPU 温度 | `76.25C` |
| 最高输入功耗 | `26068mW`，约 `26.1W` |
| Swap | 结束附近曾出现少量 Swap 使用，未导致测试失败 |
| 自动保护 | 未触发 `85C` 保护 |
| 稳定性现象 | 未观察到重启、SSH 断连、进程异常退出或测试卡死 |

`stress-ng` 结果摘要：

```text
stress-ng: info: successful run completed in 1200.12s (20 mins, 0.12 secs)
stress-ng: info: cpu      33179
stress-ng: info: vm    43825566
stress-ng: info: matrix 6344374
```

测试结束后远程复查：

```bash
pgrep -a stress-ng
pgrep -a gpu_stress
nvpmodel -q
```

其中 `stress-ng` 和 `gpu_stress` 无残留进程，`nvpmodel -q` 仍显示：

```text
NV Power Mode: 40W
4
```

## 6. 结论

在未接入相机、雷达和整车动力系统的条件下，C1902 V1.1 载板上的 Orin NX 16GB 已完成 `40W` 模式下 CPU + GPU + 内存综合压力测试。

本次结论：

1. 计算侧综合压力测试通过；
2. GPU 能够被 CUDA 压力程序拉到高负载，`GR3D_FREQ` 基本维持 `99%`；
3. CPU、GPU 和内存压力同时存在时，最高 `tj / cpu` 为 `80.468C`，未触发 `85C` 自动停止保护；
4. 最高输入功耗约 `26.1W`，说明该综合压力未吃满 `40W` 上限；
5. 当前结果支持继续推进后续真实业务负载测试和装车适配检查。

## 7. 边界与后续

本次测试不表示以下项目已经完成：

1. 相机实际采集链路；
2. Mid360 供电与数据链路；
3. Orin NX 与 STM32 UART 联调；
4. ROS2 人工接管逻辑；
5. 真实模型推理和传感器融合负载；
6. 整车装车后的长时间温升、线束、载板供电区域热点和机械固定验收；
7. 40W 上限被真实业务完整吃满时的长期稳定性。

后续建议：

1. 接入相机、雷达和必要供电支路后，进行真实业务负载 30 分钟以上测试；
2. 装车后重点复查载板 DC 输入口、电感、供电芯片、M.2 SSD 附近和线束弯折半径；
3. 若真实业务中 `tj / cpu` 长时间接近或超过 `85C`，应优先优化风道、散热器接触、风扇策略或功耗模式。
