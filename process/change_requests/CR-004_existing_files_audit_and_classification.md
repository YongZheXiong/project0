# CR-004：全项目已有文件只读审计与分类

## 状态
已完成

## 日期
2026-05-08

## 发起原因
Project0 已建立最小治理骨架、AI 工作流规范、文档治理规范和治理入口文件。为了在继续 P1.3 之前确保当前已有文件能够作为后续项目基石，需要对当前仓库中已有文件做一轮只读审计与分类，识别事实冲突、颗粒度不一致、文件状态不清、旧规划误导、占位文件伪装正式文档、陈旧描述和 P1.3 前置风险。

## 变更目标
1. 对当前已有文件进行只读审计；
2. 按文档层级检查文件职责和状态；
3. 识别事实冲突、颗粒度不一致、职责混乱、陈旧表述和状态不清；
4. 重点复核 `file_structure_design_proposal.md` 是否存在“规划方案被误读为当前真实目录”的风险；
5. 识别 P1.3 前必须修复的问题；
6. 识别可以后续修复的问题；
7. 输出后续分批修复建议；
8. 不修改任何业务文档；
9. 为后续 CR-005、CR-006、CR-007 等实际修复提供依据。

## 影响范围
本 CR 创建阶段只创建 CR-004 文件。

后续执行阶段将进行只读审计，可能读取以下范围：
1. `README.md`
2. `AGENTS.md`
3. `CHANGELOG.md`
4. `docs/DOC_INDEX.md`
5. `docs/_meta/conventions/`
6. `process/change_requests/`
7. `process/decisions/`
8. `docs/00_definition/`
9. `docs/01_planning/`
10. `docs/02_architecture/`
11. `docs/04_deployment/`
12. `hardware/`
13. `src/`
14. `firmware/`
15. `config/`
16. `scripts/`
17. `reports/`
18. `presentation/`
19. `experiments/`
20. `simulation/`
21. `data/`

后续执行阶段可能创建审计报告：
1. `docs/_meta/audit/g0_existing_files_audit_2026-05-08.md`

## 允许修改的文件
本 CR 创建阶段只允许创建：
1. `process/change_requests/CR-004_existing_files_audit_and_classification.md`

后续执行阶段允许创建：
1. `docs/_meta/audit/g0_existing_files_audit_2026-05-08.md`

后续执行阶段不允许修改已有业务文件。

## 禁止修改的文件
1. `process/decisions/`
2. `docs/00_definition/`
3. `docs/01_planning/`
4. `docs/02_architecture/`
5. `docs/04_deployment/`
6. `README.md`
7. `AGENTS.md`
8. `CHANGELOG.md`
9. `docs/DOC_INDEX.md`
10. `docs/_meta/conventions/`
11. `hardware/`
12. `src/`
13. `firmware/`
14. `config/`
15. `scripts/`
16. `reports/`
17. `presentation/`
18. `experiments/`
19. `simulation/`
20. `data/`

## 涉及 DEC
不直接修改 DEC。后续只读审计可检查 DEC 状态、引用关系和下游承接情况，但不得修改 DEC 结论。

## 审计重点
1. 文件状态是否清楚：正式 / 草案 / 占位 / 废弃 / 异常待复核 / 规划方案 / 低完成度但有效；
2. 文件颗粒度是否合理；
3. 是否存在一个文件同时承担事实源、索引、执行计划和复盘记录；
4. 是否存在 README、DOC_INDEX、CHANGELOG 等治理文件反向定义技术事实；
5. 是否存在规划方案文件被误读为当前真实状态；
6. 是否存在未来阶段内容被写成当前完成状态；
7. 是否存在 DEC 与规划层、架构层不一致；
8. 是否存在 P1.3 硬件命名、人工接管、电源边界、急停边界、传感器型号等前置冲突；
9. 是否存在占位文件伪装成正式文档；
10. 是否存在需要后续新增 DEC_INDEX、硬件命名基线或文件状态索引的必要性。

## 问题分类要求
后续审计报告必须将问题分为三类：

### A 类：P1.3 前必须修复
会影响 BOM、采购清单、硬件事实、接线、人工接管、安全边界或 Agent 后续判断的问题。

### B 类：G0 阶段建议修复
会影响文档规范、颗粒度、状态清晰度或后续维护，但不直接阻塞 P1.3 的问题。

### C 类：暂缓处理
属于 P2-P6、P7-P10 或未来阶段的内容；当前只需标注状态，不应展开修复。

## 风险评估
如果不进行本轮审计，当前已有文件中的旧规划、占位内容、状态不清、事实冲突或下游误读可能继续影响 P1.3 BOM、采购清单、硬件边界和后续 Agent 判断。

本 CR 本身只建立审计入口，不修改业务文档。主要风险是后续审计范围扩大为无边界重写，因此后续执行必须保持只读审计，并将实际修复拆分到后续 CR。

## 执行计划
1. 人工确认 CR-004；
2. Codex / Agent 进行只读全项目审计；
3. 输出 `docs/_meta/audit/g0_existing_files_audit_2026-05-08.md`；
4. 人工复核审计报告；
5. 根据审计报告拆分后续修复 CR；
6. 关闭 CR-004。

## 验证清单
1. CR-004 已建立；
2. 后续审计阶段不修改已有业务文件；
3. 审计报告按 A / B / C 分类；
4. 审计报告覆盖定义层、规划层、架构层、DEC、治理层、占位层；
5. 审计报告明确指出 `file_structure_design_proposal.md` 的状态和风险；
6. 审计报告不提出无限制重写项目；
7. 审计报告不要求补写未来阶段完整内容；
8. 没有修改 DEC；
9. 没有提前创建 P1.3 BOM 或采购清单；
10. git diff 只包含批准范围内文件。

## 回滚方式
如果 CR-004 创建阶段需要回滚，可删除 CR-004 文件；如果后续审计报告已提交，可通过 `git revert` 回滚对应 commit。

## 最终结果
- 已完成全项目已有文件只读审计与分类；
- 审计范围包括项目定义层、规划层、架构层、DEC、部署/实现/测试/报告层、占位文件；
- 发现 A 类问题（P1.3 前必须修复）若干条（例如硬件命名基线、人工接管链路、急停边界、file_structure_design_proposal.md 状态不清）；
- 发现 B 类问题若干条（文档颗粒度不统一、旧规划描述、占位文件状态不明确等）；
- 发现 C 类问题若干条（未来阶段内容、低优先级占位文件、P2-P6/P7-P10规划方案）；
- 审计报告生成路径：docs/_meta/audit/g0_existing_files_audit_2026-05-08.md；
- 未修改任何已有文件；
- 后续可根据报告拆分 CR-005、CR-006、CR-007 等分批修复。

## 关联 commit
<81510c2> docs(audit): add G0 existing files audit report
