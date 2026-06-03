# Fusion 360 电源托盘超详细建模步骤 v0.1

本文用于在 Fusion 360 中手工重建 Project0 电源托盘模型。单位全部为 mm。

## 0. 建模目标

建一个用于固定 132 mm x 67.7 mm x 56 mm 电池的低墙电源托盘。

托盘由以下结构组成：

1. 3 mm 厚矩形底板。
2. 15 mm 高、3 mm 厚分段限位墙。
3. 两条魔术贴绑带对应的四个圆角槽。
4. 四个 M3 安装孔。
5. 底部 EVA 泡棉覆盖区。

## 1. 新建文件与单位

1. 打开 Fusion 360。
2. 新建一个 Design。
3. 保存文件，建议命名为 `power_tray_v0_1`。
4. 在左侧 Browser 中确认 Document Settings。
5. 点击 Units。
6. 确认单位为 `mm`。
7. 如果不是 mm，点击 Change Active Units，改为 `Millimeter`。

## 2. 建议先建立用户参数

路径：Modify -> Change Parameters。

建议建立以下 User Parameters：

| 参数名 | 数值 | 单位 | 含义 |
|---|---:|---|---|
| battery_L | 132 | mm | 电池长度 |
| battery_W | 67.7 | mm | 电池宽度 |
| battery_H | 56 | mm | 电池高度 |
| inner_L | 133.5 | mm | 托盘内腔长度 |
| inner_W | 75.7 | mm | 托盘内腔宽度 |
| wall_T | 3 | mm | 限位墙厚度 |
| base_T | 3 | mm | 底板厚度 |
| wall_H | 15 | mm | 限位墙高度 |
| outer_L | inner_L + 2 * wall_T | mm | 托盘外形长度 |
| outer_W | inner_W + 2 * wall_T | mm | 托盘外形宽度 |
| slot_L | 30 | mm | 绑带槽长度 |
| slot_W | 4 | mm | 绑带槽宽度 |
| slot_R | 2 | mm | 绑带槽圆角 |
| slot_margin | 3 | mm | 槽外侧到托盘外边缘距离 |
| mount_D | 3.2 | mm | M3 通孔直径 |
| mount_offset | 8 | mm | 安装孔中心到外边缘距离 |
| eva_L | 133 | mm | EVA 长度 |
| eva_W | 75 | mm | EVA 宽度 |
| eva_T | 2 | mm | EVA 厚度 |

说明：

- `outer_L` 应得到 139.5 mm。
- `outer_W` 应得到 81.7 mm。
- 托盘总高为 `base_T + wall_H = 18 mm`。

## 3. 建立坐标约定

建议使用以下约定：

1. X 轴为电池长度方向。
2. Y 轴为电池宽度方向。
3. Z 轴为高度方向。
4. 模型中心在托盘中心。
5. 底板底面在 Z = 0。
6. 底板上表面在 Z = 3。
7. 限位墙顶面在 Z = 18。

这样后续检查尺寸最直观。

## 4. 建底板

1. 点击 Create Sketch。
2. 选择 XY 平面。
3. 用 Center Rectangle 画一个中心矩形。
4. 矩形中心点选择原点。
5. 输入尺寸：
   - X 方向：`outer_L`
   - Y 方向：`outer_W`
6. Finish Sketch。
7. 选中矩形轮廓。
8. 点击 Create -> Extrude。
9. Distance 输入 `base_T`。
10. Operation 选择 New Body。
11. 确认底板尺寸为 139.5 mm x 81.7 mm x 3 mm。

## 5. 画内腔参考矩形

这一步主要用于后续定位墙体和 EVA，不一定拉伸实体。

1. 点击 Create Sketch。
2. 选择底板上表面。
3. 用 Center Rectangle 画一个中心矩形。
4. 中心点选择原点。
5. 输入尺寸：
   - X 方向：`inner_L`
   - Y 方向：`inner_W`
6. 将这个矩形线改为 Construction。
7. Finish Sketch。

内腔参考矩形尺寸应为 133.5 mm x 75.7 mm。

## 6. 建短边限位墙

短边限位墙用于限制电池沿 X 方向滑动，因此建议连续。

1. 点击 Create Sketch。
2. 选择底板上表面。
3. 在 X 负方向画第一个短边墙矩形。
4. 这个矩形的尺寸为：
   - X 方向：`wall_T`
   - Y 方向：`outer_W`
5. 矩形中心 X 坐标为：
   - `-(inner_L / 2 + wall_T / 2)`
6. 矩形中心 Y 坐标为 0。
7. 再在 X 正方向画第二个短边墙矩形。
8. 第二个矩形中心 X 坐标为：
   - `inner_L / 2 + wall_T / 2`
9. 第二个矩形中心 Y 坐标为 0。
10. Finish Sketch。
11. 选中两个短边墙轮廓。
12. Extrude。
13. Distance 输入 `wall_H`。
14. Direction 选择 One Side，向上。
15. Operation 选择 Join。

完成后短边墙应从 Z = 3 拉到 Z = 18。

## 7. 建长边分段限位墙

长边墙需要在绑带槽位置断开，避免绑带被连续侧墙挡住。

### 7.1 计算分段位置

绑带有两条，沿 X 方向分布在内腔四分之一和四分之三附近。

推荐两个绑带中心 X 坐标：

- 左侧绑带中心：`-inner_L / 4 = -33.375 mm`
- 右侧绑带中心：`inner_L / 4 = 33.375 mm`

每个槽长度为 30 mm。为了让墙体不顶到绑带，墙体断开宽度建议：

- `slot_L + 8 = 38 mm`

因此每个绑带位置前后各断开 19 mm。

两个断开区间为：

- 左断开区间：-52.375 mm 到 -14.375 mm
- 右断开区间：14.375 mm 到 52.375 mm

长边墙剩余三段：

- 左段：-69.75 mm 到 -52.375 mm
- 中段：-14.375 mm 到 14.375 mm
- 右段：52.375 mm 到 69.75 mm

其中 69.75 mm 是外形长度的一半。

### 7.2 画上侧长边墙

1. 点击 Create Sketch。
2. 选择底板上表面。
3. 画三个矩形，Y 方向都为 `wall_T`。
4. 三个矩形的 Y 中心坐标为：
   - `inner_W / 2 + wall_T / 2`
   - 也就是 39.35 mm。
5. 三个矩形 X 范围分别为：
   - -69.75 到 -52.375
   - -14.375 到 14.375
   - 52.375 到 69.75
6. 如果用 Center Rectangle，三个矩形宽度分别为：
   - 17.375 mm
   - 28.75 mm
   - 17.375 mm
7. Finish Sketch。
8. 选中三个轮廓。
9. Extrude。
10. Distance 输入 `wall_H`。
11. Operation 选择 Join。

### 7.3 镜像下侧长边墙

方法 A，推荐：

1. 选中刚刚做出的上侧三个长边墙特征。
2. 点击 Create -> Mirror。
3. Pattern Type 选择 Features。
4. Mirror Plane 选择 XZ 平面。
5. 确认生成下侧长边墙。

方法 B：

按 7.2 同样画三个矩形，但 Y 中心坐标改为 -39.35 mm。

## 8. 建绑带槽

绑带槽是底板上的通槽。每条绑带需要左右两侧各一个槽，共四个槽。

### 8.1 槽的位置

槽中心 X 坐标：

- `-inner_L / 4 = -33.375 mm`
- `inner_L / 4 = 33.375 mm`

槽中心 Y 坐标：

- 上侧：`outer_W / 2 - slot_margin - slot_W / 2`
- 数值：40.85 - 3 - 2 = 35.85 mm
- 下侧：-35.85 mm

因此四个槽中心为：

- (-33.375, 35.85)
- (33.375, 35.85)
- (-33.375, -35.85)
- (33.375, -35.85)

### 8.2 画圆角槽草图

1. 点击 Create Sketch。
2. 选择底板上表面。
3. 在第一个槽中心附近画一个 Center Slot。
4. 槽方向沿 X 方向。
5. 槽总长输入 `slot_L = 30 mm`。
6. 槽宽输入 `slot_W = 4 mm`。
7. 让槽中心约束到对应坐标，例如 (-33.375, 35.85)。
8. 按同样方法画其余三个槽。
9. Finish Sketch。

### 8.3 切穿槽

1. 选中四个槽轮廓。
2. 点击 Extrude。
3. Direction 选择向下。
4. Distance 输入 `base_T`，或选择 Extent Type -> Through All。
5. Operation 选择 Cut。
6. 确认四个槽完全贯穿底板。

槽切完后检查：

- 槽外侧离托盘外边缘约 3 mm。
- 槽内侧靠近电池底面边缘。
- 槽没有切进短边限位墙。
- 长边限位墙在槽位处已经断开。

## 9. 建四角安装孔

安装孔用于把托盘固定到小车底板，当前按 M3 通孔处理。

### 9.1 孔中心位置

托盘外形一半尺寸：

- X 半长：69.75 mm。
- Y 半宽：40.85 mm。

孔中心到外边缘距离为 8 mm，因此孔中心坐标为：

- X：±61.75 mm。
- Y：±32.85 mm。

四个孔中心为：

- (-61.75, 32.85)
- (61.75, 32.85)
- (-61.75, -32.85)
- (61.75, -32.85)

### 9.2 使用 Hole 工具建孔

1. 点击 Create -> Hole。
2. Placement 选择 From Sketch 或 At Point。
3. 如果使用草图点，先在底板上表面画四个点并标注上述坐标。
4. Hole Type 选择 Simple。
5. Diameter 输入 `mount_D = 3.2 mm`。
6. Extent 选择 Through All。
7. Operation 选择 Cut。

如果准备用沉头螺钉：

1. Hole Type 改为 Countersink。
2. 通孔仍为 3.2 mm。
3. 沉头角度和直径按实际螺钉填写。
4. 目标是螺钉头不高出底板上表面。

注意：

- 当前 STL 只建了 3.2 mm 通孔。
- 如果加工方要实际装配，建议根据真实螺钉补沉头或沉孔。

## 10. 建 EVA 参考体

EVA 不一定要作为托盘实体导出，但强烈建议在 Fusion 中建一个单独组件或透明参考体，用来检查覆盖范围。

1. 新建 Component，命名为 `EVA_pad_reference`。
2. Create Sketch。
3. 选择底板上表面。
4. 用 Center Rectangle 画中心矩形。
5. 输入尺寸：
   - X 方向：`eva_L = 133 mm`
   - Y 方向：`eva_W = 75 mm`
6. Finish Sketch。
7. Extrude。
8. Distance 输入 `eva_T = 2 mm`。
9. Operation 选择 New Body。
10. 给 EVA 参考体设置半透明材质或单独颜色。

检查：

- EVA 在限位墙内侧。
- EVA 没有顶住限位墙。
- EVA 覆盖四角安装孔。
- 电池底面放在 EVA 上。

正式导出托盘 STL 时，可以隐藏 EVA 参考体。

## 11. 建电池参考体

为了检查装配关系，建议建立一个电池占位体。

1. 新建 Component，命名为 `Battery_reference`。
2. Create Sketch。
3. 选择 EVA 上表面或底板上表面。
4. 用 Center Rectangle 画中心矩形。
5. 输入尺寸：
   - X 方向：`battery_L = 132 mm`
   - Y 方向：`battery_W = 67.7 mm`
6. Finish Sketch。
7. Extrude。
8. Distance 输入 `battery_H = 56 mm`。
9. Operation 选择 New Body。
10. 如果从底板上表面画，则将电池参考体向上移动 `eva_T = 2 mm`。

检查：

- 电池长度方向总间隙约 1.5 mm。
- 电池宽度方向总间隙约 8 mm。
- 电池底面位于 EVA 上方。
- 限位墙高 15 mm，没有超过鼓包安全距离。

正式导出托盘 STL 时，隐藏电池参考体。

## 12. 倒角和圆角

推荐在托盘实体上做以下处理：

1. 绑带槽上口边缘：Fillet R1 到 R2。
2. 绑带槽下口边缘：轻微倒角或 R0.5 到 R1。
3. 电池可能接触的内侧墙边：Fillet R1。
4. 限位墙顶部内外边：Fillet R1。
5. 托盘外侧底边：小倒角 0.5 mm 或 R0.5。
6. 安装孔上口：倒角 0.3 mm 到 0.5 mm。

如果 Fusion 报错：

- 优先保留绑带槽圆角。
- 其次保留电池接触内边圆角。
- 外侧装饰圆角可以降低半径或取消。

## 13. 装配检查清单

在 Fusion 中打开 Inspect -> Measure，逐项检查：

1. 托盘外形是否为 139.5 mm x 81.7 mm。
2. 托盘内腔是否为 133.5 mm x 75.7 mm。
3. 底板厚度是否为 3 mm。
4. 限位墙高度是否为 15 mm。
5. 托盘总高是否为 18 mm。
6. 绑带槽是否为 30 mm x 4 mm。
7. 槽中心是否在 X = ±33.375 mm。
8. 槽中心是否在 Y = ±35.85 mm。
9. 安装孔直径是否为 3.2 mm。
10. 安装孔中心是否在 X = ±61.75 mm, Y = ±32.85 mm。
11. EVA 是否为 133 mm x 75 mm x 2 mm。
12. 电池参考体是否能自然放入。
13. 电池长度方向是否几乎不能滑动。
14. 绑带是否能从槽中穿过。
15. 绑带拉紧路径是否不压充电线。
16. 托盘未设计手指抓取位是否符合车体层间距。

## 14. 导出文件

### 14.1 导出 STL

1. 在 Browser 中隐藏 `Battery_reference`。
2. 隐藏 `EVA_pad_reference`。
3. 只保留托盘实体可见。
4. 右键托盘 Body 或 Component。
5. 选择 Save as Mesh。
6. Format 选择 STL。
7. Unit Type 选择 Millimeter。
8. Refinement 选择 High。
9. 保存为 `power_tray_v0_1.stl`。

### 14.2 导出 STEP

如果需要给机械加工或进一步 CAD 修改：

1. 隐藏电池参考体和 EVA 参考体。
2. File -> Export。
3. Type 选择 STEP。
4. 保存为 `power_tray_v0_1.step`。

### 14.3 保存 Fusion 原生文件

1. 保存当前设计。
2. File -> Export。
3. Type 选择 F3D。
4. 保存为 `power_tray_v0_1.f3d`。

## 15. 发给加工方时建议附带的信息

给别人加工或 3D 打印时，建议同时说明：

1. 文件单位是 mm。
2. 用途是电池托盘。
3. 推荐材料 PETG。
4. 底板贴平台打印。
5. 安装孔按 M3 通孔。
6. 螺钉头不能高出底板上表面。
7. EVA 会覆盖孔位。
8. 绑带槽需要去毛刺，不能割绑带。
9. 内侧接触电池位置需要圆滑处理。
10. 这是 v0.1 设计稿，首件应先试装，不建议一次性批量加工。


