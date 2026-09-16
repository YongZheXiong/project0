# H60 safe-control firmware

本目录保存 Project0 面向 OpenCTR H60 V3.7 / STM32F407VET6 的安全控制固件、默认关闭的运动候选以及宿主测试。

## 默认安全边界

默认 `make firmware` 构建保持：

- `MOTION=0 / CAL=0`，上电默认 `DISARMED`；
- 八路 H 桥输入先锁为 GPIO 低电平；
- ARM 在运动条件未满足时返回 `MOTION_LOCKED`；
- STOP、DISARM、通信超时、协议错误、断言、HardFault 与 IWDG 路径统一撤销输出；
- 运动审计、单通道表征、四轮固定 profile 和复位诊断均使用独立编译门，不能泄漏到默认制品。

## 隔离构建

| 入口 | 作用 | 关键限制 |
| --- | --- | --- |
| `make motion-audit-firmware` | 编译运动控制路径供离线审计 | `CAL=0`，仍不能 ARM |
| `make m2a-verify` | 单通道短租约校准候选 | 每次 ARM 仅一通道/方向，75 ms 非零租约 |
| `make h6-characterization-firmware` | H6 单通道固定档位表征候选 | 默认关闭，不是生产参数 |
| `make w2-four-wheel-profile-firmware` | 四轮固定 80‰ 前/后 profile | 每次 ARM 固定方向，换向必须 STOP 后重新 ARM |
| `make w2-five-second-link-loss-firmware` | 五秒绝对 ARM 上限候选 | 仍保留 75 ms 命令租约；仅用于断链验证 |
| `make iwdg-diagnostic-firmware` | IWDG/HardFault 复位诊断 | 强制 `MOTION=0`，与运动构建互斥 |

这些入口只生成可审计制品，不构成刷写、接电机或运动授权。

## 验证

```bash
make test
make sanitize
make source-safety-test
make motion-lock-test
make firmware
make verify
make w2-four-wheel-profile-test
make w2-five-second-link-loss-test
```

测试覆盖状态机、协议、调度周期、输出提交前中断、超时/STOP 清零、IWDG 诊断隔离、非法编译组合拒绝和 ARM 构建检查。ARM 交叉编译需要 GNU Arm Embedded 工具链；宿主测试使用系统 C 编译器与 Python 3。

## 当前证据边界

- 四轮最终线束架空前进、后退和 STOP 已形成 H60-only 受限证据。
- 真实 USB-COM 断开后的四轮停车有数字记录和双机视频支持，但没有视频—串口独立时钟校准，不能宣称精确停轮时间。
- 当前结果不覆盖上位机链路、单侧掉电反供电、带载、落地、低电量、热、长时、电流/PWM 波形或完整 H6-H8。
- 最终生产参数与完整 P2 资格仍由后续验收决定。

公开摘要见 [`../../reports/h60_no_orin_w2_m3_v1_1_2.md`](../../reports/h60_no_orin_w2_m3_v1_1_2.md)。
