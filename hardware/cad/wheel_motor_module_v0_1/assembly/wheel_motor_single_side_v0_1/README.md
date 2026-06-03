# Wheel Motor Single Side Assembly v0.1

状态：v0.1 单侧轮系装配基线已归档。

本目录用于保存单侧轮系装配 CAD 文件。该装配由 85 mm 轮胎、6 mm 抱紧式联轴器、JGB37-520 带编码器减速电机和 JGB37 电机支架组成，用于验证轮胎、联轴器、电机轴、支架姿态和第一层底板缺口之间的几何关系。

参数来源：

1. `hardware/cad/chassis_layer1/design_inputs.md`
2. `hardware/cad/wheel_motor_module_v0_1/parts/wheel_85mm_v0_1/`
3. `hardware/cad/wheel_motor_module_v0_1/parts/coupler_6mm_clamp_v0_1/`
4. `hardware/cad/wheel_motor_module_v0_1/parts/motor_jgb37_520_v0_1/`
5. `hardware/cad/wheel_motor_module_v0_1/parts/motor_bracket_jgb37_v0_1/`
6. 用户在 Fusion 360 中的装配检查结果。

当前装配关系：

1. 电机支架底盘安装面用于贴合第一层底板下方。
2. 电机安装在支架电机安装面一侧。
3. 联轴器与电机输出轴同轴连接。
4. 轮胎与联轴器同轴连接。
5. 该装配为单侧轮系，不包含左右镜像、车体底板和轮胎缺口实体。

关键检查结果：

1. 支架贴底板面到轮轴中心距离：约 `33.673 mm`。
2. 轮胎内侧到支架电机安装面外侧距离：约 `9.1 mm`。
3. 轮胎内侧到第一排支架底部孔中心距离：正常伸出状态下约 `19.2 mm`。
4. 轮胎内侧到第二排支架底部孔中心距离：约 `43.5 mm`。
5. 第一排与第二排支架底部孔中心距差值约 `23.4 mm`，与支架底部孔距一致。

说明：

1. 用户确认电机输出轴存在少量伸缩量；缩短状态下第一排孔距离测得约 `20.1 mm`，正常完全伸出状态下约 `19.2 mm`。
2. 该装配用于 v0.1 几何验证，不代表最终加工装配图。
3. 后续左右镜像装配应基于本装配继续验证 `173 mm` 轮距、轮胎缺口和支架孔位。

归档文件：

1. `source/wheel_motor_single_side_v0_1.f3z`：Fusion 360 装配源文件。
2. `final/wheel_motor_single_side_v0_1.step`：已确认的 v0.1 单侧轮系装配交换文件。
3. `preview/wheel_motor_single_side_v0_1.stl`：预览和快速尺寸检查文件。

验证记录：

1. STEP 文件单位为 mm，包含实体 BREP，不是空导出文件。
2. STEP 中可识别 5 个实体 BREP。
3. STL 包围盒约为 `102.5 x 84.99 x 84.99 mm`。


