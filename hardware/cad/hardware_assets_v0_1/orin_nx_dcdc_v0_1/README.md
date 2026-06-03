# Orin NX DC-DC v0.1

状态：v0.1 单件 CAD 资产已归档，用于计算支路电源模块布局验证。

## 文件

1. `source/orin_nx_dcdc_v0_1.f3d`：Fusion 360 可编辑源文件。
2. `final/orin_nx_dcdc_v0_1.step`：STEP 交换文件，后续装配优先使用。
3. `preview/orin_nx_dcdc_v0_1.stl`：STL 预览和包围盒检查文件。

## 来源

1. 原始导出目录：`<本地CAD导出目录>/`
2. 原始文件名前缀：`Orin NX 计算支路DCDC`
3. 建模方式：用户在 Fusion 360 中按实物外形建模并导出。

## 尺寸检查

1. STL 三角面数量：`696`。
2. STL 包围盒约为 `71.57 x 15 x 34.93 mm`。
3. STEP 单位为 mm。
4. STEP 检测到 `1` 个实体 BREP、`1` 个 closed shell 和 `16` 个 advanced face。

## 使用说明

1. 用于 Orin NX 独立供电模块在第一层或第二层的摆放、端子朝向和线束空间验证。
2. 当前模型按外形包络使用，不替代电气接线、保险配置或散热验证。
3. 后续装配时需额外考虑垫柱高度、导线弯折、防拉扯固定和输入/输出极性标识空间。
