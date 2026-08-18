# Wheel Motor Module v0.1

状态：草案，独立轮系零件建模与装配验证模块。

本目录用于分别建立 Project0 轮胎、联轴器、电机和电机支架的独立 3D 模型，再进行单侧装配与当前 `175 mm` 轮距下的左右镜像装配验证。

当前文件：

1. `parts/motor_bracket_jgb37_v0_1/`
   - JGB37 电机支架单零件 CAD 基线。
   - `final/jgb37_motor_bracket_v0_1.step` 为后续装配优先使用文件。

2. `parts/motor_jgb37_520_v0_1/`
   - JGB37-520 带编码器减速电机单零件 CAD 基线。
   - `final/jgb37_520_motor_v0_1.step` 为后续装配优先使用文件。

3. `parts/coupler_6mm_clamp_v0_1/`
   - 6 mm 抱紧式六角联轴器单零件 CAD 基线。
   - `final/clamp_coupler_6mm_v0_1.step` 为后续装配优先使用文件。

4. `parts/wheel_85mm_v0_1/`
   - 85 mm 天然橡胶轮胎单零件 CAD 基线。
   - `final/wheel_85mm_v0_1.step` 为后续装配优先使用文件。

5. `source/fusion_auto_model_wheel_motor_module_v0_1.py`
   - Fusion 360 Python 参数化建模脚本。
   - 分别生成轮胎、联轴器、电机和电机支架模型，再生成单侧轮系模块和左右镜像检查模块。

6. `assembly/`
   - 存放单侧轮系和左右镜像装配文件。

7. `assembly/wheel_motor_single_side_v0_1/`
   - 单侧轮系装配 v0.1 CAD 基线。
   - `final/wheel_motor_single_side_v0_1.step` 为后续左右镜像装配优先使用文件。

8. `assembly/wheel_motor_left_right_v0_1/`
   - 左右轮系装配 v0.1 CAD 基线。
   - 采用 `175 mm` 轮距，左右轮系外包宽度约 `208.4 mm`。
   - `final/wheel_motor_left_right_v0_1.step` 为后续第一层底板缺口、支架孔位和轮距复核优先使用文件。

9. `preview/`
   - 后续存放预览 STL、截图或中间检查文件。

10. `final/`
   - 后续确认后存放导出文件。

说明：

1. 本模块不是最终加工图。
2. 参数来自第一层底盘设计输入、商家尺寸图和用户补充参数。
3. 电机支架、JGB37-520 电机、6 mm 抱紧式联轴器和 85 mm 轮胎已有单零件 CAD 基线。
4. 单侧轮系装配已有 v0.1 CAD 基线。
5. 左右轮系装配已有 v0.1 CAD 基线；此前 `173 mm` 轮距版本几何上极限可行，但编码器间距约 `1.4 mm`，当前基线改用 `175 mm` 轮距。
6. 输出轴 D 面、联轴器锁紧螺丝、轮毂细节和轮胎胎纹仍待后续按需要精细化。
7. 后续应基于左右轮系装配继续验证第一层底板缺口、电机支架孔位、编码器间距和线束避让，再将结果回写到第一层底盘总装草模。
