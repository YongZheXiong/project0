# CR-008：G0 收束状态与治理文档最终对齐

## CR 编号

CR-008

## 标题

G0 收束状态与治理文档最终对齐

## 状态

草案

## 日期

2026-05-08

## 发起原因

G0 主要治理修复已经完成，CR-005、CR-006、CR-007 均已闭环。当前需要在回到 P1.3 主线前，对治理规则与入口文件做最后一次状态级收尾，避免 `ai_workflow.md` 被 G0 专用章节污染为阶段性文档，避免 `document_governance.md` 中普通文档状态与 CR 流程状态混淆，并清理 `AGENTS.md`、`DOC_INDEX.md`、`README.md`、`CHANGELOG.md` 中可能残留的过期 G0 表述。

## 变更目标

1. 删除 `ai_workflow.md` 中“## 8. 当前 G0 治理阶段使用规则”整节；
2. 检查 `ai_workflow.md` 中是否还有其他把该文件限制为 G0 阶段使用的表述，并做最小修正；
3. 在 `document_governance.md` 中补充 CR 流程状态说明，明确 CR 状态与普通文档状态不同；
4. 检查 `AGENTS.md` 中是否仍写“正在 G0 治理收束”，如有则更新为“G0 核心收束已完成，当前回到 P1.3 主线”；
5. 检查 `docs/DOC_INDEX.md` 中是否还有过期治理待办或 CR 范围陈旧描述；
6. 检查 `README.md` 当前状态是否需要从“governance 治理中”更新为“G0 收束完成，回到 P1.3”；
7. 检查 `CHANGELOG.md` 是否已记录 CR-004 至 CR-007 及本轮最终治理收尾；
8. 不修改 DEC，不修改业务架构，不创建 BOM 或采购清单。

## 影响范围

本 CR 创建阶段只创建 CR-008 文件。

后续执行阶段可能修改：

- `docs/_meta/conventions/ai_workflow.md`
- `docs/_meta/conventions/document_governance.md`
- `AGENTS.md`
- `docs/DOC_INDEX.md`
- `README.md`
- `CHANGELOG.md`

## 允许修改的文件

本 CR 创建阶段只允许创建：

- `process/change_requests/CR-008_g0_final_governance_cleanup.md`

后续执行阶段可能允许修改：

- `docs/_meta/conventions/ai_workflow.md`
- `docs/_meta/conventions/document_governance.md`
- `AGENTS.md`
- `docs/DOC_INDEX.md`
- `README.md`
- `CHANGELOG.md`

## 禁止修改的文件

- `process/decisions/`
- `docs/00_definition/`
- `docs/01_planning/`
- `docs/02_architecture/`
- `docs/_meta/audit/`
- `hardware/`
- `src/`
- `firmware/`
- `config/`
- `scripts/`
- `reports/`
- `presentation/`
- `experiments/`
- `simulation/`
- `data/`
- 未来目录创建
- P1.3 BOM 或采购清单

## 涉及 DEC

无直接 DEC 修改。

## 风险评估

如果不做本轮收尾，`ai_workflow.md` 可能继续被误读为 G0 专用文档，`document_governance.md` 可能混淆普通文档状态与 CR 流程状态，`AGENTS.md`、`DOC_INDEX.md`、`README.md`、`CHANGELOG.md` 中的过期 G0 表述可能误导后续 Agent 和人工操作。

## 执行计划

1. Plan：只读检查六个治理文件中的 G0 专用表述、CR 状态表述和过期待办；
2. Execute：仅在批准范围内做状态级小修；
3. Verify：检查无 DEC、业务文档、实现层和未来目录修改；
4. Commit：人工查看 diff 后提交，并关闭 CR-008。

## 验证清单

1. `ai_workflow.md` 不再包含 G0 专用章节；
2. `ai_workflow.md` 仍作为全阶段通用 AI 工作流规范；
3. `document_governance.md` 已区分普通文档状态与 CR 流程状态；
4. `AGENTS.md`、`docs/DOC_INDEX.md`、`README.md`、`CHANGELOG.md` 不再出现误导性的“G0 正在进行”表述；
5. `CHANGELOG.md` 记录本轮 G0 收束结果；
6. 未修改 DEC；
7. 未修改业务架构；
8. 未创建 BOM 或采购清单；
9. `git diff` 只包含批准范围内文件。

## 回滚方式

如果 CR-008 创建阶段需要回滚，可删除 CR-008 文件；如果后续执行阶段已经提交，可通过 `git revert` 回滚对应 commit；如果尚未提交，可通过 `git restore` 回滚批准范围内文件。

## 最终结果

待填写。

## 关联 commit

未提交。
