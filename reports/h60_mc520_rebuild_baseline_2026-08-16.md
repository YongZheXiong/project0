# H60 + MC520 重建与公开仓库统一报告

> 日期：2026-08-16
> 结论：数字基线已统一；实物、上电和运动仍未放行。

## 已解决的主要矛盾

- 主要入口从 STM32 + WSDC2412D + JGB37-520 切换为 H60 V3.7 + MC520P56。
- 旧 83-85mm 轮、CPR、三层 CAD 和 Stage D/E 只保留历史意义；新平台采用 65mm 轮、新 CAD 和 H0-H8。
- Mid360 与 Orin 均使用独立电源支路，不从 H60 供电。
- 主保险和四个支路保险均保留；额定由线束、端子和实测冻结。
- 急停 NC 控继电器切 H60，NO 只做 Orin 3.3V GPIO 干接点反馈。
- 急停复位依靠 H60 安全启动与 Orin 显式 ARM 防止自动运动，不增加独立硬件复位按钮。
- Keyes 分压板移除，H60 PC0 采 VIN；ACS712 首版不安装。
- H60 TVS 不作为急停、保险或主 VIN 瞬态保护的替代。
- 新增 Orin 保活、H60 失电情况下的 UART 反供电验证门。

## 未关闭项

到货和版本、支路额定、继电器 DC 分断、AT8236 限流与 MC520 负载能力、回生浪涌、UART 反供电、Orin GPIO/pinmux、Mid360 低输入与峰值、安全固件、新 CAD、编码器标定和落地运动均需实测。

H60 失电后 PC0 VIN 遥测也会消失，首版没有急停后的独立电池/SOC 遥测。

## 公开参考

- OpenCTR H60：https://www.xtark.cn/product/show.php?itemid=7
- MC520：https://www.xtark.cn/product/show.php?itemid=25
- Livox Mid360：https://www.livoxtech.com/mid-360/specs
- NVIDIA Jetson Orin 载板规范：https://developer.nvidia.com/downloads/assets/embedded/secure/jetson/orin_nano/docs/jetson_orin_nano_devkit_carrier_board_specification_sp.pdf
