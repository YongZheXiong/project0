# 电源托盘设计记录 v0.1

状态：设计记录，待首件打印与实物试装复核。

本文记录电源托盘的机械设计取舍。本文不是 DEC，不改变电源架构、BOM、采购状态、接线边界或安全机制。

## 设计对象

电源托盘用于固定 Project0 小车主电池，使电池在车体内具备基础限位、绑带固定和可维护拆装能力。

电池本体尺寸按 132 mm x 67.7 mm x 56 mm 设计，电池底面为 132 mm x 67.7 mm 面。

电池中部存在输出线和充电线引出的鼓包。鼓包距离电池底面约 15 mm，因此托盘限位墙高度不超过 15 mm，托盘平面尺寸不考虑鼓包外形。

## 结构选择

本设计采用矩形底板、分段限位墙和两条魔术贴绑带组合。

选择理由：

1. 矩形底板便于 FDM 3D 打印和装车固定。
2. 分段限位墙可以限制电池水平滑动，同时给绑带槽留出路径。
3. 限位墙高度 15 mm，避免干涉电池鼓包，同时保证低墙可拆卸。
4. 魔术贴绑带负责竖向约束，限位墙负责水平约束。
5. 底部 EVA 泡棉隔离安装孔和螺钉头，降低电池底面磨损风险。

## 关键参数

1. 托盘外形：139.5 mm x 81.7 mm x 18 mm。
2. 托盘内腔：133.5 mm x 75.7 mm。
3. 底板厚度：3 mm。
4. 限位墙厚度：3 mm。
5. 限位墙高度：15 mm。
6. 安装孔：M3 通孔，直径 3.2 mm。
7. 绑带槽：30 mm x 4 mm。
8. 绑带：宽 26 mm，厚 1.3 mm。
9. EVA 建议尺寸：133 mm x 75 mm x 2 mm。

## 文件位置

最终 Fusion 导出文件位于：

1. `hardware/cad/power_tray/final/power_tray_v0_1_fusion_final.f3d`
2. `hardware/cad/power_tray/final/power_tray_v0_1_fusion_final.step`
3. `hardware/cad/power_tray/final/power_tray_v0_1_fusion_final.stl`

建模源文件和说明位于：

1. `hardware/cad/power_tray/source/fusion_auto_model_power_tray.py`
2. `hardware/cad/power_tray/source/power_tray_v0_1.scad`
3. `hardware/cad/power_tray/source/fusion_modeling_steps.md`

## 非目标

1. 不表示电池托盘已经打印完成。
2. 不表示电池托盘已经装车验收。
3. 不改变电池、保险、开关、接线或电源架构结论。
4. 不替代 BOM、采购清单或电源架构文档。

## 待首件复核

1. 电池是否能自然放入，不需要用力按压。
2. 电池长度方向是否基本不能移动。
3. 绑带是否能顺畅穿过槽口。
4. 绑带拉紧后是否不压线、不顶墙。
5. 螺钉头是否不会穿透 EVA 接触电池底面。
6. 托盘装车后是否仍能方便取出充电线。
7. PETG 打印件强度和边缘处理是否满足实际使用。


