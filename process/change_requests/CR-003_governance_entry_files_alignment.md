# CR-003：治理入口文件对齐

## 状态
草案

## 日期
2026-05-08

## 发起原因
CR-002 已经建立 AI 工作流规范和文档治理规范。为了让后续 G0 全项目已有文件规范化收束能够稳定执行，需要将 `AGENTS.md`、`docs/DOC_INDEX.md`、`README.md`、`CHANGELOG.md` 与新治理规则对齐，避免入口文件之间出现陈旧描述、重复定义、职责不清或与当前治理流程不一致的问题。

## 变更目标
1. 让 `AGENTS.md` 引用或承接 `ai_workflow.md` 与 `document_governance.md`；
2. 修正 `docs/DOC_INDEX.md` 中关于 `process/change_requests/`、`docs/_meta/` 等治理目录的陈旧描述；
3. 确认 `README.md` 作为仓库入口摘要，不反向定义事实源；
4. 在 `CHANGELOG.md` 的 Unreleased 中记录本轮 governance 治理变更；
5. 明确 `AGENTS.md`、`docs/DOC_INDEX.md`、`README.md`、`CHANGELOG.md` 的职责边界；
6. 为后续 CR-004 全项目已有文件审计提供一致入口。

## 影响范围
本 CR 创建阶段只创建 CR-003 文件。

后续执行阶段可能修改：
1. `AGENTS.md`
2. `docs/DOC_INDEX.md`
3. `README.md`
4. `CHANGELOG.md`

## 允许修改的文件
本 CR 创建阶段只允许创建：
1. `process/change_requests/CR-003_governance_entry_files_alignment.md`

后续执行阶段可能允许修改：
1. `AGENTS.md`
2. `docs/DOC_INDEX.md`
3. `README.md`
4. `CHANGELOG.md`

## 禁止修改的文件
1. `process/decisions/`
2. `docs/00_definition/`
3. `docs/01_planning/`
4. `docs/02_architecture/`
5. `docs/_meta/conventions/ai_workflow.md`
6. `docs/_meta/conventions/document_governance.md`
7. `hardware/`
8. `src/`
9. `firmware/`
10. `config/`
11. `scripts/`
12. `reports/`
13. `presentation/`
14. `experiments/`
15. `simulation/`

## 涉及 DEC
无直接 DEC 修改。

## 风险评估
如果不进行入口文件对齐，后续 Agent 可能继续读取到陈旧入口信息，例如 `process/change_requests/` 当前未建、治理规则未落地、`README.md` 与 `docs/DOC_INDEX.md` 职责边界不清、`CHANGELOG.md` 未记录治理变更等，从而增加后续全项目整理时的误改风险。

## 执行计划
1. 人工确认 CR-003；
2. 修改 `AGENTS.md`，使其引用 `ai_workflow.md`、`document_governance.md`、`docs/DOC_INDEX.md` 和 change requests 机制；
3. 修改 `docs/DOC_INDEX.md`，修正关于 `process/change_requests/` 和 `docs/_meta/` 的状态描述；
4. 检查 `README.md` 是否仍与当前治理状态一致，如无必要则少改或不改；
5. 修改 `CHANGELOG.md`，在 Unreleased 中记录本轮治理变更；
6. 验证四个入口文件之间没有职责冲突；
7. 关闭 CR-003。

## 验证清单
1. CR-003 已建立；
2. `AGENTS.md` 与 `ai_workflow.md` / `document_governance.md` 关系清楚；
3. `docs/DOC_INDEX.md` 不再出现 `process/change_requests/` 当前未建等陈旧描述；
4. `README.md` 仍然只是仓库入口摘要；
5. `CHANGELOG.md` 记录 governance 治理变更；
6. 没有修改 DEC；
7. 没有修改业务架构文档；
8. 没有扩大到 P1.3 BOM、采购清单或未来阶段内容；
9. git diff 只包含批准范围内文件。

## 回滚方式
如果 CR-003 创建阶段需要回滚，可删除该 CR 文件；如果后续执行阶段已经提交，可通过 `git revert` 回滚对应 commit。

## 最终结果
待填写。

## 关联 commit
未提交。
