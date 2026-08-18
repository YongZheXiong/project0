# Hardware Assets

## 当前基线

Project0 当前采用 H60 V3.7 + 4 × MC520P56_12V + 65mm 轮，整车 CAD 重新设计。主要入口：

- [当前数字 BOM](bom.md)
- [H60 电源与急停接线](wiring/h60_power_estop_wiring_v0_1.md)
- [H0-H8 验收计划](../docs/06_testing/p2_h60_mc520_rebuild_acceptance_plan_2026-08-16.md)
- [当前整车 CAD](cad/current_vehicle_v0_2/README.md)

当前公开 CAD 包含 28 个 STEP。第二轮数字复审确认全部 B-Rep 有效，轴距 `170 mm`、轮距约 `184.16 mm`，两层采用 6 根支柱，D435 水平安装。两层铝板、D435 支架和 Mid360 平台已委托加工，但尚未交付、试装或验收。

## 历史资产

原三层底盘、JGB37-520 轮系、STM32/WSDC 接线、ACS712 和电源托盘资料保留用于解释上一实车的设计与测试。旧 CAD 已集中归档到 [`archive/cad_legacy_pre_h60_2026-08-18/`](archive/cad_legacy_pre_h60_2026-08-18/)，不再是当前加工、采购、接线或仿真基线。旧资产中的“已完成/已装车/已通过”只对当时平台成立。

H60/MC520 套件、线束和整车其他实物状态仍需后续确认；数字 CAD 有效性不替代加工公差、结构强度或实物验收。
