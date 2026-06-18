# Hardware Assets

本目录存放 Project0 的硬件台账、采购相关文件和硬件设计资产。

## 当前内容

1. `bom.md`
   - P1.3 硬件 BOM。

2. `hardware_inventory.md`
   - 已有硬件盘点。

3. `missing_hardware_list.md`
   - 缺失硬件和采购相关清单。

4. `wiring/wire_selection_v0_1.md`
   - 当前线材、线径、端子和模块间连接采购口径。
   - 该文件不是最终接线图，不表示线束已经制作、装车或验证完成。

5. `wiring/acs712_current_sensing_wiring_v0_1.md`
   - ACS712 电流采样、分压滤波和 STM32 ADC 接线说明。

6. `wiring/p2_power_estop_bringup_summary_2026-06-16.md`
   - P2 电源分支、急停动力切断和 USB 反供电现象的公开技术摘要。

7. `wiring/p2_stm32_power_fault_summary_2026-06-17.md`
   - STM32 控制板 3.3V 供电故障、隔离边界和替换板验收顺序。

8. `cad/power_tray/`
   - 电源托盘 CAD 设计稿、Fusion 最终导出文件、设计记录和加工交付说明。
   - 最终 3D 打印文件位于 `cad/power_tray/final/`。

9. `cad/hardware_assets_v0_1/`
   - 整车布局验证用硬件单件 CAD 资产归档。
   - 当前作为历史单件资产库和装配引用来源，不作为最终底板加工基线。

10. `cad/wheel_motor_module_v0_1/`
   - 轮系、电机、支架、联轴器和左右轮系装配 CAD 资料。

11. `cad/chassis_layer1/`、`cad/chassis_layer2/`
   - 早期第一层 / 第二层底板草模和布局验证资料。
   - 当前作为历史验证资料保留，不作为最终加工图目录。

12. `cad/chassis_three_layer_freeze_v0_1/`
   - 三层底盘最终冻结 CAD 包，包括三层底板、三层装配、整车装配和必要支撑件。
   - 当前作为三层底板加工输入、结构复查和后续实物装配对照基线。

## 注意

`cad/power_tray/` 当前表示电源托盘设计稿已形成，不表示托盘已经打印、装车或验收完成。

`cad/chassis_three_layer_freeze_v0_1/` 当前表示三层底盘结构和布局进入本轮加工冻结基线，不表示底板已经加工完成、装车完成、接线完成或验收完成。

`wiring/wire_selection_v0_1.md` 当前表示线材、线径和端子采购口径已形成，不表示线束已经制作、装车、上电或验收完成。

急停动力切断已完成基础验证，但线束最终固定、UART、编码器、长期温升和落地运动仍未闭环。原 STM32 控制板当前处于 3.3V 供电故障隔离状态。

早期 CAD 草案和验证目录保留用于追溯建模过程；当前加工与装配复查优先引用 `cad/chassis_three_layer_freeze_v0_1/`。


