# OpenCTR H60 部署入口

适用控制器为 OpenCTR H60 V3.7 / STM32F407。当前公开成果使用 Nano 的 USB-A 端口连接 H60 USB-COM；旧 Orin NX 板载 UART 记录按当时配置保存。

[v1.1.3 架空验证报告](../../reports/nano_h60_raised_control_v1_1_3.md)对应独立工程固件 28R2 和原 MC520P56 轮组。后续轻弧探索使用另一工程构建，旧轮组的落地转向尚未达成目标。当前工程暂停。

## 无设备构建与测试

- [固件源码](../../firmware/h60_safe_control/README.md)提供 `make verify` 和归档试验制品重建说明。
- [ROS 2 源码](../../src/README.md)提供单元检查及隔离 launch。默认生产运动开关关闭，目标上限为零。
- [P2 验收计划](../06_testing/p2_h60_mc520_rebuild_acceptance_plan_2026-08-16.md)用于核对实物配置与覆盖范围。无电机、架空与落地证据分别适用。

H60 上报 VIN，当前无车载分路电流测量。外置主开关管理车辆电源。USB-COM 在单侧掉电时的电气边界仍有未覆盖工况。
