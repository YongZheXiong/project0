# OpenCTR H60 部署入口

> 状态：目标版本 H60 V3.7，实物部署尚未开始。

H60 负责四路 MC520P56 电机与编码器。Orin 通过受保护 UART 通信；永久接线前必须关闭 H60 掉电反供电风险。PC0 VIN ADC 承接电池电压监测；Orin 和 Mid360 不从 H60 供电。板载开关保持 ON，外部主开关管理整车，急停继电器切 H60 支路。

到货后依次完成：版本/丝印/针序核对、可复现固件构建、不接电机限流上电、VIN ADC 校准、安全固件、UART 反供电保护、H0-H8 验收。厂商示例功能不能自动关闭 Project0 的 ARM、超时、看门狗、热和回生安全门。

产品参考：https://www.xtark.cn/product/show.php?itemid=7
