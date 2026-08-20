# STM32 USART3 最小发送测试记录

## 1. 测试目标

该临时固件用于验证 STM32 USART3 到 Orin NX 的最小单向发送链路，不属于正式底盘控制固件。

计划行为：

1. 使用 USART3；
2. 波特率 `115200`；
3. 周期发送固定测试文本；
4. 电驱 PWM 保持为 `0`；
5. 不执行任何电机动作。

## 2. 接线边界

UART 只连接：

- STM32 TX → Orin NX RX；
- STM32 RX ← Orin NX TX；
- STM32 GND ↔ Orin NX GND。

UART 不连接 5V，TX / RX 必须交叉，双方使用 3.3V TTL 电平。

## 3. 当前状态

固件方案和串口参数已形成。原 STM32 控制板曾发生 3.3V 供电故障，因此当时暂停烧录和 Orin NX 收包验证。

后续替换板已完成供电、SWD、USART3 和 Orin NX 收包验证；Orin NX 可读取 STM32 周期输出，STM32 收到测试文本后可回传 ACK。

UART 物理链路和最小双向测试成立；正式控制协议、通信中断停车、无新指令停车和动力测试当时仍未完成。
