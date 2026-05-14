# CR-015: C-15 DEC 格式统一

## 状态

已完成

## 背景

C-15 只读审计发现，`process/decisions/DEC-*.md` 中存在状态字段名称、状态值写法、阶段字段名称、日期格式、标题格式和正文结构不一致的问题。

本 CR 用于为 DEC 文件格式统一建立受控边界，避免在格式整理过程中误改技术结论、状态含义、日期事实、替代关系或历史事实。

## 问题

当前 DEC 文件主要存在以下格式差异：

1. 状态字段写法不一致，例如 `状态`、`决策状态`、`## 状态`。
2. 状态值写法不一致，例如 `确认`、`已确认`、`异常占位 / 非有效事实源`。
3. 阶段字段写法不一致，例如 `阶段`、`所属阶段`。
4. 日期格式不一致，例如 `2026/4/17`、`2026-04-19`。
5. 标题和正文层级不一致，例如 `## 决策`、`## 内容`、编号章节混用。
6. 示例、异常占位、废弃和确认 DEC 混在同一目录中，需要保留不同状态边界。

## 修改范围

本 CR 只处理 DEC 文件格式统一。

允许讨论和后续人工确认的修改类型包括：

1. 统一状态字段名称。
2. 统一状态值写法。
3. 统一阶段字段名称。
4. 统一日期展示格式，但不改变日期事实。
5. 统一标题和正文结构。
6. 调整模板文件，使后续 DEC 有一致格式依据。

## 不修改范围

本 CR 不允许执行以下修改：

1. 不改变任何 DEC 的技术结论。
2. 不改变任何 DEC 的状态含义。
3. 不改变日期事实。
4. 不改变替代 / 被替代关系。
5. 不把异常占位 DEC 改成有效 DEC。
6. 不把废弃 DEC 改成确认 DEC。
7. 不修改 Architecture、Planning、README、AGENTS、CHANGELOG、DOC_INDEX。
8. 不修改硬件、BOM、采购、源码、固件、Docker、服务、构建、部署相关文件。

## 格式统一原则

建议后续统一采用以下元信息字段：

1. `状态`
2. `阶段`
3. `日期`
4. `关联 CR`
5. `替代 / 被替代关系`

建议状态值写法为：

1. `确认`
2. `草案`
3. `废弃`
4. `异常占位 / 非有效事实源`
5. `示例`

上述写法只用于格式统一，不改变任何 DEC 的实际状态含义。

## 第一批建议修改文件

第一批建议处理文件为：

1. `process/decisions/DEC-000_example.md`
2. `process/decisions/DEC-012-sensor_mounting_layout.md`
3. `process/decisions/DEC-018-manual_takeover_input_scheme.md`
4. `process/decisions/DEC-019-emergency_stop_layout.md`
5. `process/decisions/DEC-020-battery_mounting_scheme.md`
6. `process/decisions/DEC-021-motor_driver_layout.md`

第一批只建议处理格式差异明显、风险相对可控的文件。是否执行必须经人工确认。

## 执行结果

第一批 DEC 格式统一已完成，涉及文件为：

1. `process/decisions/DEC-000_example.md`
2. `process/decisions/DEC-012-sensor_mounting_layout.md`
3. `process/decisions/DEC-018-manual_takeover_input_scheme.md`
4. `process/decisions/DEC-019-emergency_stop_layout.md`
5. `process/decisions/DEC-020-battery_mounting_scheme.md`
6. `process/decisions/DEC-021-motor_driver_layout.md`

本轮未修改以下特殊 DEC：

1. `process/decisions/DEC-009-semantic_location_owned_by_ap_manager.md`：异常占位 / 非有效事实源，保持不动。
2. `process/decisions/DEC-013-manual_takeover_and_estop.md`：废弃 DEC，保持不动。
3. `process/decisions/DEC-022-semantic_location_ownership_boundary.md`：确认 DEC 但结构特殊，保持不动。

本轮没有改变以下内容：

1. 技术结论。
2. 状态含义。
3. 日期事实。
4. 替代 / 被替代关系。
5. 历史事实。

## 验证结果

本轮验证结果如下：

1. 未发现越界修改。
2. 未发现技术事实变化。
3. `git diff --check` 仅有 LF/CRLF warning。

## 特殊 DEC 处理原则

1. `process/decisions/DEC-000_example.md` 是模板，不是事实源。
2. `process/decisions/DEC-009-semantic_location_owned_by_ap_manager.md` 是异常占位 / 非有效事实源，不得被格式统一误改为有效 DEC。
3. `process/decisions/DEC-013-manual_takeover_and_estop.md` 是废弃 DEC，不得被格式统一误改为确认 DEC。
4. `process/decisions/DEC-022-semantic_location_ownership_boundary.md` 是确认 DEC，但当前采用 `## 状态` 结构，是否统一元信息区需单独人工确认。
5. DEC-009、DEC-013、DEC-022 作为特殊文件，需单独处理或单独人工确认。

## 验证方式

后续如进入 Execute，至少执行以下验证：

1. `git status --short`
2. `git diff --name-only`
3. `git diff --check`
4. 检查实际修改文件是否只包含人工批准文件。
5. 检查是否未改变任何 DEC 技术结论。
6. 检查是否未改变任何 DEC 状态含义。
7. 检查是否未改变日期事实。
8. 检查是否未改变替代 / 被替代关系。
9. 检查是否未把异常占位 DEC 改成有效 DEC。
10. 检查是否未把废弃 DEC 改成确认 DEC。

## 风险与约束

主要风险：

1. 将格式统一误做成技术结论改写。
2. 将 `确认` / `已确认` 的文字统一误解为状态变化。
3. 将日期格式统一误做成日期事实变更。
4. 将 DEC-009 异常占位误改为普通确认 DEC。
5. 将 DEC-013 废弃记录误改为普通确认 DEC。
6. 对 DEC-022 元信息结构调整时误触碰其语义位置归属边界结论。

约束：

1. 本 CR 必须先完成 Plan，再经人工确认后才能 Execute。
2. Execute 只能修改人工批准的文件。
3. 如果格式统一需要影响 DOC_INDEX、CHANGELOG 或其他治理入口，应另行说明影响范围并等待人工确认。
4. 本 CR 不发布版本。
