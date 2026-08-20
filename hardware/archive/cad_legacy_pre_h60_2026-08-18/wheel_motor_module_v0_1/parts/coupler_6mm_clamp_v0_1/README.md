# 6 mm Clamp Coupler v0.1

状态：v0.1 单零件基线已归档，关键特征简化模型。

本目录用于保存 6 mm 抱紧式六角联轴器的单零件 CAD 模型。该模型用于电机输出轴、联轴器和轮胎的装配验证，重点表达外包络、内孔、轴孔深度、右侧伸出段和锁紧避让相关特征。

参数来源：

1. `hardware/archive/cad_legacy_pre_h60_2026-08-18/chassis_layer1/reference_drawings/联轴器.webp`
2. `hardware/archive/cad_legacy_pre_h60_2026-08-18/chassis_layer1/design_inputs.md`
3. 用户补充：联轴器为 `6 mm` 抱紧式。

当前建模范围：

1. 外径：约 `Φ20 mm`。
2. 内孔：约 `Φ6 mm`。
3. 抱紧主体高度 `h1`：约 `11 mm`。
4. 轴孔深度 `h2`：约 `11.8 mm`。
5. 右侧伸出段：约 `6.5 mm`。
6. 总长：约 `17.5 mm`。
7. 锁紧螺丝相关结构：按关键外包络和避让特征简化建模。

暂不建模：

1. 螺纹真实牙型。
2. 锁紧螺丝实体。
3. 制造倒角、表面处理和弹性夹紧变形。

归档文件：

1. `source/clamp_coupler_6mm_v0_1.f3d`：Fusion 360 可编辑源文件。
2. `final/clamp_coupler_6mm_v0_1.step`：已确认的 v0.1 单零件实体交换文件，后续装配优先使用。
3. `preview/clamp_coupler_6mm_v0_1.stl`：预览和快速尺寸检查文件。

验证记录：

1. STL 包围盒约为 `20.0 x 17.5 x 20.0 mm`。
2. 侧面圆柱识别结果：主体约 `Φ20 x 11 mm`，右侧伸出段约 `6.5 mm`。
3. 内孔约 `Φ6 mm`，轴孔深度约 `11.8 mm`。
4. STEP 文件单位为 mm，且包含实体 BREP，不是空导出文件。
