# CR-002：AI 工作流与文档治理规则固化

## 状态
草案

## 日期
2026-05-08

## 发起原因
项目已通过 governance 分支完成第一轮最小治理，包括 DOC_INDEX 补全、change_requests 建立、README 对齐、DEC-013 异常处理和人工接管链路对齐。
为了避免后续 AI 使用混乱、跨文件修改失控，需要固化 AI 工作流与文档治理规则。

## 变更目标
1. 建立 docs/_meta/conventions/ai_workflow.md；
2. 建立 docs/_meta/conventions/document_governance.md；
3. 明确对话式 AI、Codex / Agent、人工、Git 分工；
4. 明确 Plan → Execute → Verify → Commit 工作流；
5. 明确何时必须建立 CR；
6. 明确 DEC、CR、README、CHANGELOG、DOC_INDEX、架构文档、占位文件职责；
7. 明确事实源、文件颗粒度、占位、废弃、规划方案管理规则；
8. 为后续 CR-003、CR-004、CR-005 和 P1.3 提供规则依据。

## 影响范围
- 本阶段只创建 CR-002 文件
- 后续执行阶段可能创建：
  - docs/_meta/conventions/ai_workflow.md
  - docs/_meta/conventions/document_governance.md

## 允许修改
- process/change_requests/CR-002_ai_workflow_and_document_governance.md

## 禁止修改
- process/decisions/
- docs/00_definition/
- docs/01_planning/
- docs/02_architecture/
- README.md
- AGENTS.md
- CHANGELOG.md
- hardware/
- src/
- firmware/

## 执行计划
1. 人工确认 CR-002
2. 创建 ai_workflow.md
3. 创建 document_governance.md
4. 验证规则文档简洁可执行
5. 关闭 CR-002