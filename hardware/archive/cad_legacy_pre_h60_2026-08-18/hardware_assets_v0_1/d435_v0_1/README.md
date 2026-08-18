# Intel RealSense D435 v0.1

状态：v0.1 单件 CAD 资产已归档，用于前向视觉安装和整车空间验证。

## 文件

1. `source/intel_realsense_d435_v0_1.f3d`：Fusion 360 可编辑源文件。
2. `final/intel_realsense_d435_v0_1.step`：STEP 交换文件，后续装配优先使用。
3. `preview/intel_realsense_d435_v0_1.stl`：STL 预览和包围盒检查文件。

## 来源

1. 原始导出目录：`<本地CAD导出目录>/`
2. 原始文件名前缀：`Intel Realsense D435`
3. 建模方式：用户在 Fusion 360 中导入/整理并导出。

## 尺寸检查

1. STL 三角面数量：`101954`。
2. STL 包围盒约为 `89.904 x 25 x 25.05 mm`。
3. STEP 单位为 mm。
4. STEP 未检测到 `MANIFOLD_SOLID_BREP`，但包含 `27` 个 closed shell 和 `4473` 个 advanced face，按外壳/多壳体参考模型使用。

## 使用说明

1. 用于 D435 前向安装位置、视野无遮挡、安装支架和线缆预留的空间验证。
2. 当前模型不替代 D435 官方机械图和实物量测。
3. 后续若增加 D435 安装支架或 USB 线缆弯折包络，应另建装配或新增版本。
