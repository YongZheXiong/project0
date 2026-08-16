# P2 H60 + MC520 当前实现基线

> 状态：已批准数字基线；尚未确认采购、到货、接线、上电或运动。

## 系统拓扑

```text
3S battery -> 25A main fuse -> main switch -> fused distribution
  ├─ H60 fuse -> relay 30/87 -> H60 -> 4 x MC520P56
  ├─ Orin fuse -> 12V DC/DC -> Orin NX -> D435 / gamepad
  ├─ Mid360 fuse -> 12V buck-boost -> Mid360
  └─ coil fuse -> estop NC -> relay coil

estop NO -> 3.3V dry-contact GPIO feedback -> Orin NX
Orin NX <-> protected UART <-> H60
```

## 职责

| 实体 | 当前职责 |
| --- | --- |
| Orin NX | ROS2、感知、定位、导航、人工/自动仲裁、急停锁存、显式 ARM 和日志 |
| H60 | 四路编码器、四路电驱、速度闭环、本地超时、看门狗、故障撤 PWM 和 VIN ADC |
| 急停 NC + 继电器 | 独立切断 H60 正极 |
| 急停 NO | 通过外部 3.3V 上拉和限流向 Orin 提供干接点状态 |
| Orin/Mid360 DC-DC | 两条相互独立的 12V 支路，不经 H60 |

## 历史映射

| 上一平台 | 当前平台 |
| --- | --- |
| STM32F407 + 2 × WSDC2412D | OpenCTR H60 V3.7 |
| JGB37-520 + 83-85mm 轮 | MC520P56_12V + 65mm 轮 |
| Keyes 分压 + ACS712 | H60 PC0 VIN ADC；首版无板载电流遥测 |
| 三层冻结 CAD | 新整车 CAD |
| 旧 Stage D/E 与 CPR | H0-H8 从零重新验收 |

## 恢复语义

急停按下使继电器释放、H60 失电，而 Orin/Mid360 保活。急停机械复位只恢复 H60 的供电条件；H60 必须冷启动到 `DISARMED/PWM=0`，Orin 必须保持急停锁存，只有自检、心跳和新鲜命令通过后的新会话显式 ARM 才能运动。

## 阻断项

线束/保险/继电器额定、UART 反供电、H60 安全固件、电流/温升/回生、Mid360 瞬态稳定性、新 CAD 和 H0-H8 均未关闭。H60 失电时 VIN ADC 无法持续上报，此可观测性缺口在首版中明确保留。
