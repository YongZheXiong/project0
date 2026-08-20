# H60 + MC520 重建与公开仓库统一报告

> 日期：2026-08-16
> 更新：2026-08-20
> 结论：公开数字基线已统一；实物、上电和运动仍未放行。

## 已解决的主要矛盾

- 主要入口从 STM32 + WSDC2412D + JGB37-520 切换为 H60 V3.7 + MC520P56。
- 旧 83-85mm 轮、CPR、三层 CAD 和 Stage D/E 只保留历史意义；新平台采用 65mm 轮、新 CAD 和 H0-H8。
- Mid360 与 Orin 均使用独立电源支路，不从 H60 供电。
- 主保险、主开关与 H60/Orin/Mid360 三条支路保护保留；支路额定由线束、端子和实测冻结。
- 当前不安装独立急停按钮、继电器、急停 GPIO、Keyes 或 ACS712；主开关只作人工整车断电，不称急停。
- H60 必须实现默认 DISARMED、显式 ARM、STOP/DISARM、命令超时、IWDG、异常撤 PWM 和重启后禁止自动恢复运动。
- H60 PC0 采 VIN；当前没有车载电流遥测。外部仪表只产生台架测试证据。
- H60 的 TVS、驱动内部保护和 VIN ADC 都不能替代主保险、支路保护或实测验收。
- 新增 H60/Orin 任一侧掉电时的 UART 反供电验证门。
- 上一平台照片、接线和硬件台账转入历史归档，不再作为当前接线或运动准入依据。

## 未关闭项

到货和版本、支路额定、AT8236 限流与 MC520 负载能力、回生浪涌、UART 反供电、Mid360 低输入与峰值、H60 运动控制固件、机械试装、编码器标定和落地运动均需实测。

H60 失电后 PC0 VIN 遥测也会消失，首版没有独立电池/SOC 遥测。

## 当前公开入口

- [H60 当前电源、运动约束与采样边界](../docs/02_architecture/h60_power_motion_sampling_boundary.md)
- [H60 电源接线基线](../hardware/wiring/h60_power_wiring_v0_2.md)
- [H60 运动控制固件要求](../firmware/h60_motion_control_firmware_requirements_v0_2.md)
- [H0-H8 重建验收计划](../docs/06_testing/p2_h60_mc520_rebuild_acceptance_plan_2026-08-16.md)

## 公开参考

- OpenCTR H60：https://www.xtark.cn/product/show.php?itemid=7
- MC520：https://www.xtark.cn/product/show.php?itemid=25
- Livox Mid360：https://www.livoxtech.com/mid-360/specs
- NVIDIA Jetson Orin 载板规范：https://developer.nvidia.com/downloads/assets/embedded/secure/jetson/orin_nano/docs/jetson_orin_nano_devkit_carrier_board_specification_sp.pdf
