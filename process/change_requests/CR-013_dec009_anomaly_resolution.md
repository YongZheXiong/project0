# CR-013: DEC-009 异常处理与替代 DEC 路线确认

## 状态

已完成

## 背景

`process/decisions/DEC-009-semantic_location_owned_by_ap_manager.md` 文件存在但为空。

DEC-009 当前没有状态字段、日期、标题或决策结论，不可作为有效 DEC 技术事实源。

历史审计和 CR 均将 DEC-009 视为异常 / 暂缓 / 待人工确认，未批准将其直接补写为正式技术结论。

C-16 DEC-009 异常处理只读审计已完成。

人工已选择处理路线 E：新建替代 DEC，DEC-009 保留异常说明。

## 覆盖问题

1. C-16：DEC-009 异常处理。

## 只读审计结论

1. DEC-009 路径：`process/decisions/DEC-009-semantic_location_owned_by_ap_manager.md`
2. 文件大小：0 字节。
3. 文件为空。
4. 无状态、无日期、无标题、无决策结论。
5. 不可作为有效技术决策事实源。
6. `docs/DOC_INDEX.md` 有异常 / 暂缓引用。
7. CR-001、CR-007、CR-009 等历史记录均未批准补写 DEC-009。
8. 未发现明确替代 DEC-009 的其他 DEC。

## 人工选择的处理路线

1. 本 CR 采用选项 E。
2. DEC-009 不直接补成正式技术事实。
3. DEC-009 后续应保留异常说明。
4. 如需承接 semantic location / AP Manager / 语义位置归属相关技术决策，应另建替代 DEC。
5. 替代 DEC 的编号、标题、范围和是否立即创建，需要后续只读 Plan 与人工确认。

## 建议后续候选修改范围

以下仅为候选范围，不在本次创建 CR 草案阶段执行：

1. `process/decisions/DEC-009-semantic_location_owned_by_ap_manager.md`
2. 一个待确认的新替代 DEC 文件。
3. `docs/DOC_INDEX.md`
4. `process/change_requests/CR-013_dec009_anomaly_resolution.md`

## 明确排除范围

1. 不修改除 DEC-009 和待确认替代 DEC 外的其他 DEC。
2. 不修改 Architecture。
3. 不修改 README、AGENTS、CHANGELOG。
4. 不修改硬件、BOM、采购、源码、固件、Docker、服务、构建、部署文件。
5. 不创造未经确认的 semantic location / AP Manager 技术事实。
6. 不把 DEC-009 写成有效确认决策。
7. 不删除 DEC-009。

## 执行原则

1. 先确认替代 DEC 的编号、标题、范围和关系。
2. DEC-009 只能写为异常说明 / 非有效事实源。
3. 替代 DEC 如创建，初始状态必须由人工确认。
4. 若替代 DEC 只是草案，不得写成已确认技术事实。
5. 所有修改必须经过 Plan → Execute → Verify → Commit。

## 风险

1. 误把空 DEC 补成未经确认事实。
2. 误删 DEC-009 造成编号和历史追溯断裂。
3. 新替代 DEC 与 DEC-009 关系不清。
4. 语义位置归属问题提前固化，影响后续语义导航 / AP Manager 设计。
5. DOC_INDEX 与 DEC 状态不同步。

## 验证方式

1. `git status --short`
2. `git diff --name-only`
3. `git diff --check`
4. 检查是否只修改批准文件。
5. 检查 DEC-009 是否未被写成有效事实源。
6. 检查替代 DEC 是否未被写成未经确认事实。
7. 检查 DOC_INDEX 是否与 DEC 状态一致。
8. 检查未修改 Architecture、硬件、BOM、采购、源码、固件、Docker、服务文件。

## 当前结果

CR-013 草案已创建并提交：

1. `814852186f0d1f6223c69c2506e7bde7a4da5ea1`
   `docs(cr): add CR-013 DEC-009 anomaly resolution draft`

CR-013 第一批处理已完成并提交：

1. `b841208fa1b2013d7be97132bf62e1ee09210dda`
   `docs(cr-013): add DEC-009 anomaly placeholder and DEC-022 draft`

实际修改 / 创建文件：

1. `docs/DOC_INDEX.md`
2. `process/decisions/DEC-009-semantic_location_owned_by_ap_manager.md`
3. `process/decisions/DEC-022-semantic_location_ownership_boundary.md`

DEC-009 已完成：

1. 将原 0 字节空文件改为“异常占位 / 非有效事实源”说明文件。
2. 保留 DEC-009 编号和历史追溯。
3. 明确 DEC-009 不作为有效 DEC 技术事实源。
4. 明确不得引用 DEC-009 作为 semantic location / AP Manager / 语义位置归属的已确认结论。

DEC-022 已创建：

1. 新建 DEC-022 作为替代 DEC 草案。
2. 状态为“草案 / 待确认”。
3. 用于承接语义位置归属与 p0_map_manager 边界讨论。
4. 人工确认前不得作为有效 DEC 技术事实源。

DOC_INDEX 已同步：

1. 仅同步 DEC-009 和 DEC-022 的索引状态与导航关系。
2. 未在 DOC_INDEX 中替代 DEC 下技术结论。

明确未改变：

1. DEC-005 的 YAML 语义位置表 + 规则匹配迭代一基线。
2. Architecture。
3. 接口定义。
4. 软件实现。
5. 硬件、BOM、采购、源码、固件、Docker、服务、构建、部署文件。

明确未确认：

1. 尚未确认 p0_map_manager 为语义位置归属模块。
2. 尚未确认 DEC-022 为有效技术决策。
3. 尚未确认开放集、LLM、语义地图研究路线或未来研究增强为当前完成能力。

C-16 当前状态：

1. DEC-009 空文件异常已完成治理处理。
2. 替代 DEC 草案 DEC-022 已创建。
3. DEC-022 后续是否转为确认 DEC，需要单独人工确认和后续 CR / DEC 流程。

## 后续状态同步

CR-013 初始处理完成时，DEC-022 仍为草案 / 待确认状态。

后续 CR-014 已确认 DEC-022，并完成 `docs/DOC_INDEX.md`、`docs/02_architecture/system_architecture.md` 和 `docs/02_architecture/interface_definition.md` 的必要同步。

当前 C-16 状态为：

1. DEC-009：异常占位 / 非有效事实源。
2. DEC-022：已确认，承接语义位置归属边界。

本次状态文字澄清不新增技术事实，不修改 DEC-022 正文，不将 DEC-009 补写为正式技术决策。
