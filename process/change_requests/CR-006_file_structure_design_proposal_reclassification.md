# CR-006：file_structure_design_proposal.md 定性修正

## 状态
草案

## 日期
2026-05-08

## 发起原因
CR-004 审计报告指出，`docs/01_planning/file_structure_design_proposal.md` 仍以“Git 仓库实际使用”的语气写目录树，并混合了当前存在目录、规划目录和未来目录，容易被误读为当前真实目录说明。

该问题主要影响文档状态清晰度和 Agent 认知，属于 G0 阶段建议修复项。为避免后续 Agent 按该文件创建未来目录或误判当前仓库结构，需要单独通过 CR-006 对该文件进行定性修正。

## 变更目标
1. 将 `file_structure_design_proposal.md` 明确定性为“规划方案 / 历史结构方案 / 非当前真实目录”；
2. 明确该文件不作为当前真实目录树依据；
3. 明确当前真实目录以 `README.md`、`docs/DOC_INDEX.md` 和实际 tree 输出为准；
4. 保留该文件的历史规划参考价值；
5. 标注其中未来目录、规划目录、当前目录的边界；
6. 不创建任何未来目录；
7. 不重写整个项目文件结构；
8. 不修改 DEC 结论；
9. 为后续 Agent 安全读取文件结构相关资料提供边界。

## 影响范围
本 CR 创建阶段只创建 CR-006 文件。

后续执行阶段可能修改：
1. `docs/01_planning/file_structure_design_proposal.md`
2. `docs/DOC_INDEX.md`
3. `README.md`

## 允许修改的文件
本 CR 创建阶段只允许创建：
1. `process/change_requests/CR-006_file_structure_design_proposal_reclassification.md`

后续执行阶段可能允许修改：
1. `docs/01_planning/file_structure_design_proposal.md`
2. `docs/DOC_INDEX.md`
3. `README.md`

## 禁止修改的文件
1. `process/decisions/`
2. `docs/00_definition/`
3. `docs/02_architecture/`
4. `docs/_meta/conventions/`
5. `docs/_meta/audit/`
6. `hardware/`
7. `src/`
8. `firmware/`
9. `config/`
10. `scripts/`
11. `reports/`
12. `presentation/`
13. `experiments/`
14. `simulation/`
15. `data/`
16. 未来目录创建
17. P1.3 BOM 或采购清单

## 涉及 DEC
无直接 DEC 修改。

## 风险评估
如果不修正该文件状态，Agent 可能把 `file_structure_design_proposal.md` 当作当前真实目录说明，进而误判当前仓库结构、误读未来目录状态，甚至错误建议创建 `docs/03_design/`、`docs/05_calibration/`、`docs/06_testing/`、`docs/07_iter2/` 等未来目录。

这会破坏 G0 治理收束中“当前真实状态”和“未来规划方案”的边界。

## 执行计划
1. Plan：只读复核 `file_structure_design_proposal.md` 与 `README.md`、`docs/DOC_INDEX.md`、当前真实目录树之间的差异；
2. 人工确认：确认该文件应被定性为“规划方案 / 历史结构方案 / 非当前真实目录”；
3. Execute：仅在批准范围内修改 `file_structure_design_proposal.md`，必要时小范围同步 `README.md` 或 `docs/DOC_INDEX.md`；
4. Verify：检查是否仍存在把该文件当作当前真实目录说明的表述，确认没有创建未来目录、没有修改 DEC、没有扩展 P2-P6 或 P7-P10；
5. Commit：人工查看 diff 后提交，并关闭 CR-006。

## 验证清单
1. CR-006 已建立；
2. `file_structure_design_proposal.md` 被明确定性为规划方案 / 历史结构方案 / 非当前真实目录；
3. 当前真实目录依据仍为 `README.md`、`docs/DOC_INDEX.md` 和实际仓库 tree；
4. 未创建未来目录；
5. 未修改 DEC；
6. 未重写整个 `docs/`；
7. 未创建 BOM 或采购清单；
8. `git diff` 只包含批准范围内文件。

## 回滚方式
如果 CR-006 创建阶段需要回滚，可删除该 CR 文件；如果后续执行阶段已经提交，可通过 `git revert` 回滚对应 commit；如果尚未提交，可通过 `git restore` 回滚批准范围内文件。

## 最终结果
待填写。

## 关联 commit
未提交。
