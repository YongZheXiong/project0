# CR-014: DEC-022 语义位置归属边界确认

## 状态

草案

## 背景

CR-013 已完成 DEC-009 异常处理。

DEC-009 已成为异常占位 / 非有效事实源。

DEC-022 已创建为替代 DEC 草案。

DEC-022 当前状态为“草案 / 待确认”。

本 CR 用于判断是否将 DEC-022 转为确认，并检查是否需要同步 DOC_INDEX、Architecture 或 Interface 文档。

## 覆盖问题

1. DEC-022 后续确认。
2. 语义位置表 / 语义位置数据 / 语义查询能力的归属边界。
3. p0_map_manager 与 p0_semantic_nav 的职责边界。

## 只读审计结论

1. DEC-022 当前未被有效事实源引用。
2. DEC-009 当前未被误读为有效事实源。
3. DEC-005 的 YAML 语义位置表 + 规则匹配仍是迭代一语义导航基线。
4. `software_architecture.md` 与 `interface_definition.md` 中已有较强证据支持 p0_map_manager 承接语义位置表 / 语义位置数据 / 语义查询。
5. `interface_definition.md` 中已有 `/p0/map/query_semantic_pose`、p0_map_manager、p0_semantic_nav 相关接口证据。
6. 但接口文档仍存在骨架版 / 待确认口径，因此需要 CR-014 受控确认。

## 建议确认方向

以下仅为候选确认方向，不表示已经确认：

1. 迭代一基线中，语义位置表、语义位置数据，以及语义标签到空间位姿 / 区域的映射能力，候选归属 p0_map_manager 管理。
2. p0_map_manager 候选对外提供语义位置查询能力。
3. p0_semantic_nav 候选通过查询接口向 p0_map_manager 获取语义位置对应的位姿或区域。
4. p0_semantic_nav 候选负责将查询结果转换为导航目标，或交由 p0_task_manager 组织执行。
5. 该确认方向不推翻 DEC-005。
6. 该确认方向不表示实现已完成。

## 建议后续候选修改范围

以下仅列候选范围，不在本次创建 CR 草案阶段执行：

1. `process/decisions/DEC-022-semantic_location_ownership_boundary.md`
2. `docs/DOC_INDEX.md`
3. `docs/02_architecture/software_architecture.md`
4. `docs/02_architecture/interface_definition.md`
5. `docs/02_architecture/system_architecture.md`
6. `process/change_requests/CR-014_dec022_semantic_location_boundary_confirmation.md`

## 最小优先白名单建议

第一批建议优先只考虑：

1. `process/decisions/DEC-022-semantic_location_ownership_boundary.md`
2. `docs/DOC_INDEX.md`
3. `process/change_requests/CR-014_dec022_semantic_location_boundary_confirmation.md`

Architecture / Interface 是否同步，应先在 CR-014 后续只读 Plan 中确认，不默认纳入 Execute。

## 明确排除范围

1. 不修改 DEC-005。
2. 不修改 DEC-009。
3. 不修改除 DEC-022 外的其他 DEC。
4. 不修改 Architecture 或 Interface，除非后续只读 Plan 与人工确认明确纳入。
5. 不修改 README、AGENTS、CHANGELOG。
6. 不修改硬件、BOM、采购、源码、固件、Docker、服务、构建、部署文件。
7. 不推翻 DEC-005 的 YAML 语义位置表 + 规则匹配基线。
8. 不把开放集、LLM、语义地图研究路线或未来研究增强写成当前完成。
9. 不把实现状态写成已完成。
10. 不绕过人工确认将 DEC-022 改为确认。

## 执行原则

1. 先只读确认 DEC-022 的精确确认文本。
2. 如果确认 DEC-022，必须明确保留 DEC-005 基线。
3. 如果确认 p0_map_manager 归属，必须限定为迭代一语义位置表 / 语义位置数据 / 语义查询能力边界。
4. 不写成 p0_map_manager 负责开放集语义理解、LLM、完整语义地图研究路线、任务编排策略或导航执行算法。
5. p0_semantic_nav 的边界应表述为迭代一基线通过查询接口获取位姿或区域，不写成永久唯一机制。
6. 后续如需改变语义位置归属或查询机制，必须另行通过 CR / DEC、影响范围评估和回滚边界确认。

## 风险

1. 过早确认 DEC-022 可能固化 p0_map_manager 归属。
2. 可能让下游 Agent 误以为实现已完成。
3. 可能对 Architecture / Interface 形成反向事实压力。
4. 可能被误解为推翻 DEC-005。
5. 可能把骨架接口误读为最终冻结接口。

## 验证方式

1. `git status --short`
2. `git diff --name-only`
3. `git diff --check`
4. 检查是否只修改批准文件。
5. 检查 DEC-022 是否未在未经人工确认前改成确认。
6. 检查是否未修改 DEC-005 / DEC-009。
7. 检查是否未推翻 YAML 语义位置表 + 规则匹配基线。
8. 检查是否未把开放集、LLM、语义地图或实现完成写成当前事实。
9. 检查是否未修改 Architecture / Interface，除非后续明确批准。

## 当前结果

待执行后填写。
