# H60 电源与急停接线基线 v0.1

> 状态：设计输入，尚未实装。接线前必须断开电池并按实物针序复核。

## 电源树

```text
3S battery (+)
-> 25A main fuse
-> external main switch
-> fused distribution

A: H60 fuse (start 10A) -> relay 30 -> relay 87 -> H60 (+)
B: Orin fuse (start 10A) -> Orin DC/DC -> 12V -> carrier board
C: Mid360 fuse (start 3A) -> Mid360 buck-boost -> 12V -> Mid360
D: coil fuse 1A -> estop NC -> relay 86

Common negative: battery, H60, both DC/DC inputs, relay 85
```

起始保险值只用于台架验证，最终不得超过线材、端子和设备允许值。

## 继电器与急停

| 端子 | 连接 |
| --- | --- |
| 30 | H60 支路保险输出 |
| 87 | H60 正极 |
| 85 | 共负极 |
| 86 | 1A 保险后经急停 NC 的线圈正极 |
| 87a | 不接并绝缘 |

如继电器带续流二极管，必须保持 86 为正、85 为负。NC 只控制线圈；按下急停后 H60 失电，Orin 与 Mid360 不断电。

## NO 状态反馈

```text
Orin 3.3V -> external 4.7-10k pull-up -> signal node
signal node -> estop NO -> Orin GND
signal node -> about 1k series resistor -> GPIO input
```

NO 是无源干接点，禁止接 12V。软件应消抖并锁存急停。单个 NO + 上拉不能区分“急停释放”和“反馈线断开”，因此硬件停车不能依赖该反馈。最终 GPIO、GND 和 pinmux 必须按载板资料和实物方向确认。

## UART

只连接 TX↔RX、RX↔TX 和共地。Orin 上电而 H60 断电时必须测量反灌；正式线束需使用在任一侧掉电时输出高阻、不会形成旁路的缓冲或隔离方案。此门关闭前不得固定直连 UART。

## 上电前

确认主/支路保险、极性、NC/NO、30/87、85/86、二极管方向、绝缘、应力释放和线束标识。首次 H60 上电不接电机并优先使用限流电源；首次电机测试车辆架空、低占空、轮周净空且有人直接监看。
