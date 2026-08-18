# Control DC-DC v0.1

状态：v0.1 单件 CAD 资产已归档，用于控制/传感器支路电源模块布局验证。

## 文件

1. `source/control_dcdc_v0_1.f3d`：Fusion 360 可编辑源文件。
2. `final/control_dcdc_v0_1.step`：STEP 交换文件，后续装配优先使用。
3. `preview/control_dcdc_v0_1.stl`：STL 预览和包围盒检查文件。

## 来源

1. 原始导出目录：`<本地CAD导出目录>/`
2. 原始文件名前缀：`控制支路DCDC`
3. 建模方式：用户在 Fusion 360 中按实物外形建模并导出。

## 尺寸检查

1. STL 三角面数量：`676`。
2. STL 包围盒约为 `60 x 14 x 30 mm`。
3. STEP 单位为 mm。
4. STEP 检测到 `1` 个实体 BREP、`1` 个 closed shell 和 `10` 个 advanced face。

## 使用说明

1. 用于控制支路 DC-DC 的安装位置、接线方向、垫柱高度和线束空间验证。
2. 当前模型只表达布局包络，不代表最终绝缘、防拉扯和散热方案。
3. 后续装配应与 STM32、主电池电压采样模块和 ACS712 信号侧走线一起验证。
