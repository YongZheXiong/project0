# Wheel Motor Left Right Assembly v0.1

状态：v0.1 左右轮系装配基线已归档。

本目录用于保存左右轮系装配 CAD 文件。该装配基于单侧轮系装配继续验证左右轮距、电机编码器间距、轮胎外包宽度，以及后续第一层底板缺口和电机支架孔位的几何输入。

参数来源：

1. `hardware/archive/cad_legacy_pre_h60_2026-08-18/wheel_motor_module_v0_1/assembly/wheel_motor_single_side_v0_1/`
2. `hardware/archive/cad_legacy_pre_h60_2026-08-18/wheel_motor_module_v0_1/parts/wheel_85mm_v0_1/`
3. `hardware/archive/cad_legacy_pre_h60_2026-08-18/wheel_motor_module_v0_1/parts/coupler_6mm_clamp_v0_1/`
4. `hardware/archive/cad_legacy_pre_h60_2026-08-18/wheel_motor_module_v0_1/parts/motor_jgb37_520_v0_1/`
5. `hardware/archive/cad_legacy_pre_h60_2026-08-18/wheel_motor_module_v0_1/parts/motor_bracket_jgb37_v0_1/`
6. 用户在 Fusion 360 中的左右轮系装配检查结果。

当前装配关系：

1. 左右两侧轮系基于单侧轮系装配镜像布置。
2. 左右轮距采用 `175 mm`。
3. 轮胎宽度采用 `33.4 mm`。
4. 左右轮系外包宽度约 `208.4 mm`。
5. 该装配不包含第一层底板实体、电池、电驱、保险盒和线束。

轮距调整记录：

1. 初始 `173 mm` 轮距版本几何上可行，但两个电机编码器之间距离约 `1.4 mm`，属于极限可行。
2. 为给编码器外壳、装配误差和线束避让留出更多余量，v0.1 左右轮系基线改用 `175 mm` 轮距。
3. 按初始检查结果估算，`175 mm` 轮距下编码器之间距离目标约为 `3.4 mm`。
4. 第一层底板外轮廓尚未最终定型，后续可按轮胎外边、缺口和支架孔位一起调整，不以早期 `270 x 210 mm` 初值反向限制本装配。

关键检查结果：

1. STEP 文件有效，包含实体几何数据。
2. STL 文件为有效二进制 STL。
3. STL 三角面数量为 `9120`。
4. STL 包围盒约为 `208.4 x 84.986 x 84.993 mm`。
5. `208.4 mm = 175 mm + 33.4 mm`，与当前轮距和轮胎宽度相符。

说明：

1. 该装配用于 v0.1 几何验证，不代表最终加工装配图。
2. `175 mm` 轮距是当前左右轮系基线，`173 mm` 仅保留为此前极限检查记录。
3. 编码器间距、线束走向、轮胎缺口和支架底部孔位仍需在第一层底板验证中继续复核。
4. 若后续发现编码器或线束仍存在干涉风险，可继续小幅增大轮距或调整第一层底板局部避让。

归档文件：

1. `source/wheel_motor_left_right_v0_1.f3z`：Fusion 360 装配源文件。
2. `final/wheel_motor_left_right_v0_1.step`：已确认的 v0.1 左右轮系装配交换文件。
3. `preview/wheel_motor_left_right_v0_1.stl`：预览和快速尺寸检查文件。

验证记录：

1. STEP 文件头显示由 Autodesk Translation Framework 导出，文件时间戳为 `2026-05-28T09:21:34+08:00`。
2. STEP 文件包含实体几何数据，不是空导出文件。
3. STL 文件包围盒约为 `208.4 x 84.986 x 84.993 mm`。
