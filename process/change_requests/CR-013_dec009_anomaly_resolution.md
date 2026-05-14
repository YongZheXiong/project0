# CR-013: DEC-009 异常处理与替代 DEC 路线确认

## 状态

草案

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

待执行后填写。
