# JGB37 Motor Bracket v0.1

状态：v0.1 单零件基线已归档。

本目录用于保存 JGB37 电机固定支架的单零件 CAD 模型。该模型先用于确认支架本体外形和孔槽位置，后续作为轮胎、电机、联轴器装配验证的支架输入。

参数来源：

1. `hardware/archive/cad_legacy_pre_h60_2026-08-18/chassis_layer1/reference_drawings/电机支架.webp`
2. `hardware/archive/cad_legacy_pre_h60_2026-08-18/chassis_layer1/design_inputs.md`
3. 用户已确认术语：底盘安装面、电机安装面。

当前建模范围：

1. 底盘安装面：`40 x 42.4 x 3 mm`。
2. 电机安装面：宽 `40 mm`、总高 `47 mm`、厚 `3 mm`，位于底盘安装面后边缘，外形为矩形加半圆顶；安装面下边从底板厚度上方 `3 mm` 起算。
3. 底盘安装孔：`4 x Φ4 mm`，孔距 `30 x 23.4 mm`。
4. 电机安装面中心槽：`13 x 27 mm`。
5. 电机安装孔：`6 x Φ3.2 mm`，按 `Φ31 mm` 孔圈近似，并作为真实切孔建模。
6. 底盘安装面外角：`R3 mm`。
7. L 型折弯内侧圆角：按 `R2 mm` 初值建模，后续可按实物复核调整。

暂不建模：

1. 真实冲压倒角。
2. 表面涂层厚度。
3. 支架弹性变形和制造公差。

归档文件：

1. `source/jgb37_motor_bracket_v0_1.f3d`：Fusion 360 可编辑源文件。
2. `final/jgb37_motor_bracket_v0_1.step`：已确认的 v0.1 单零件实体交换文件，后续装配优先使用。
3. `preview/jgb37_motor_bracket_v0_1.stl`：预览和快速尺寸检查文件。

验证记录：

1. STL 包围盒约为 `42.4 x 47.0 x 40.0 mm`。
2. 底部安装孔中心关系已核对为 `8.0 mm` 边距与 `23.4 x 30.0 mm` 孔距。
3. STEP 文件单位为 mm。
