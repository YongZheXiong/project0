# DOC_INDEX.md

## 1. 文件作用

本文档是项目0当前阶段的文档索引与依赖关系说明文件，面向 P1.3 硬件方案与采购。

它只负责回答四件事：
1. 项目0当前主要文档有哪些；
2. 每类文档负责什么；
3. 哪些文档是上游事实源、哪些是下游承接；
4. 修改某类内容时应同步检查哪些文件。

本文档不替代任何正式设计文档，也不替代 DEC、README、CHANGELOG 或实现层文件。它只做治理导航，不替任何技术结论下最终判定。

当前阶段不应把迭代二增强提前写成迭代一硬要求，也不应把规划方案当成当前真实目录。

---

## 2. 当前真实文档地图

### 2.1 项目治理层

| 文档 | 责任 | 定位 |
| --- | --- | --- |
| `README.md` | 仓库入口摘要 | 不是事实源，只做入口与状态快照，需与当前阶段同步 |
| `CHANGELOG.md` | 版本变更记录 | 不是设计事实源，只记录版本变化 |
| `AGENTS.md` | 协作规则 | 约束 AI / 人类工作方式，不定义项目事实 |
| `docs/DOC_INDEX.md` | 文档索引 | 治理导航，不是事实源 |
| `docs/_meta/` | 治理元数据 | 已建立治理元数据目录，`conventions/` 已包含 AI 工作流和文档治理规则，`audit/` 已包含 G0 已有文件审计报告，`templates/` 可作为后续模板目录使用 |
| `docs/_meta/conventions/ai_workflow.md` | AI 工作流规范 | 规定对话式 AI、Codex / Agent、人工决策和 Git 的分工 |
| `docs/_meta/conventions/document_governance.md` | 文档治理规范 | 规定文档事实源、颗粒度、状态、引用和修改边界 |

补充说明：`process/change_requests/` 已建立最小 CR 机制，包含 `README.md`、`CR-000_template.md` 以及 `CR-001` 至 `CR-008` 等变更记录。`process/weekly_log/` 与 `process/learning_notes/` 属于过程记录与学习沉淀，不是事实源。

### 2.2 项目定义层 `docs/00_definition/`

这组文档是项目0的最上游事实源，后续规划、架构、实现都应从这里承接。

| 文档 | 责任 | 说明 |
| --- | --- | --- |
| `system_positioning.md` | 最终系统定位 | 定义项目0做什么、不做什么 |
| `objective_constraints.md` | 客观限制 | 场地、硬件、时间、安全等硬约束 |
| `subjective_requirements.md` | 主观需求 | 可调整诉求与偏好，不是硬约束 |
| `iter1_core_capabilities.md` | 迭代一核心能力 | 迭代一平台成立的最低能力集合 |
| `iter2_enhancement_scope.md` | 迭代二增强边界 | 只描述增强空间，不回写成迭代一必做项 |
| `overall_deliverables.md` | 整体成果形态 | 定义最终要产出的成果类别 |
| `version_roadmap.md` | 版本路线 | 说明 V0 / V1 / V2 的关系 |
| `milestone_timeline.md` | 里程碑时间表 | 说明阶段节拍与大致时间顺序 |
| `project_workflow.md` | 项目流程 | 说明阶段总览、推进原则和依赖骨架 |

### 2.3 P1 规划层 `docs/01_planning/`

这组文档承接定义层，负责把迭代一范围裁剪成可执行的功能、任务和采购前置条件。

| 文档 | 责任 | 说明 |
| --- | --- | --- |
| `iter1_function_items.md` | 功能条目展开 | 负责“必须实现 / 接口预留 / 不纳入”裁剪 |
| `iter1_function_list.md` | 功能清单与技术选型 | 直接驱动架构、采购、WBS |
| `wbs.md` | 工作分解 | 当前低完成度，待补任务分解 |
| `risk_register.md` | 风险登记 | 当前低完成度，待补风险条目 |
| `file_structure_design_proposal.md` | 文件结构规划方案 | 只是规划方案，不等于当前真实目录树 |

说明：`file_structure_design_proposal.md` 里出现的 `docs/03_design/`、`docs/05_calibration/`、`docs/06_testing/`、`docs/07_iter2/` 都是规划中目录，当前仓库未创建，不能按现状引用。

### 2.4 系统架构层 `docs/02_architecture/`

这组文档承接定义层、规划层和决策层，负责把项目0拆成可落地的系统边界、接口边界和模块边界。

| 文档 | 责任 | 说明 |
| --- | --- | --- |
| `system_architecture.md` | 系统总架构 | 上位骨架，定义系统分层和主链路 |
| `compute_comm_architecture.md` | 计算与通信架构 | 定义节点职责和数据流边界 |
| `power_architecture.md` | 电源架构 | 定义供电边界与安全约束 |
| `hardware_architecture.md` | 硬件架构 | 定义实体结构、安装与布置 |
| `software_architecture.md` | 软件架构 | 定义软件包划分与职责边界 |
| `interface_definition.md` | 接口定义 | 定义 topic / service / action 与自定义消息骨架 |
| `diagrams/vehicle_hardware_topology.drawio` | 图源文件 | 当前架构图素材来源 |

### 2.5 决策事实源 `process/decisions/`

`process/decisions/` 是项目0的技术决策事实源。除示例文件外，其余 DEC 文件都应按决策记录处理，并向下游规划 / 架构 / 实现承接。

| 文件 | 状态 | 说明 |
| --- | --- | --- |
| `DEC-000_example.md` | 示例 | 仅用于示例，不是项目事实源 |
| `DEC-001` ~ `DEC-021` | 决策记录 | 属于技术决策事实源 |
| `DEC-009-semantic_location_owned_by_ap_manager.md` | 异常 | 当前为空文件，待人工确认 |
| `DEC-013-manual_takeover_and_estop.md` | 废弃 | 已废弃，不再作为人工接管、急停或电源架构事实源；人工接管以 DEC-018 为准，急停以 DEC-019 为准，电源边界以 DEC-014 为准 |
| `DEC-014-power_architecture_boundary.md` | 有效 | 电源架构主边界事实源 |

说明：DEC 文件只能作为决策事实源使用；DEC-009 暂缓复核；DEC-013 已废弃；DEC-014、DEC-018、DEC-019 分别承担电源边界、人工接管、急停事实源。

### 2.6 部署 / 实现 / 测试 / 报告层

这组目录承接架构和规划的下沉结果，当前大多还是占位或低完成度状态。

| 目录 | 责任 | 当前状态 |
| --- | --- | --- |
| `docs/04_deployment/` | 部署与运行说明 | 当前仅有骨架文件，内容很少 |
| `src/` | ROS2 软件实现 | 目前多数只是目录说明 |
| `firmware/` | STM32 固件实现 | 目前多数只是目录说明 |
| `hardware/` | 硬件资料与物料承接 | 目前尚缺 `bom.csv`、接线与照片索引 |
| `config/` | 配置文件 | 当前为占位层 |
| `scripts/` | 脚本 | 当前为占位层 |
| `reports/` | 报告 | 当前为占位层 |
| `presentation/` | 展示与答辩材料 | 当前为占位层 |
| `experiments/` | 实验材料 | 当前为占位层 |
| `simulation/` | 仿真材料 | 当前为占位层 |
| `data/` | 数据与记录 | 当前为占位层 |

---

## 3. 上游事实源与下游承接

| 上游事实源 | 主要下游 | 说明 |
| --- | --- | --- |
| `docs/00_definition/*` | `docs/01_planning/*`、`docs/02_architecture/*` | 定义先行，规划和架构只能承接 |
| `process/decisions/DEC-*` | `docs/01_planning/*`、`docs/02_architecture/*`、`docs/04_deployment/*`、`src/`、`firmware/`、`hardware/` | 决策结论向下游沉淀 |
| `docs/01_planning/iter1_function_list.md`、`iter1_function_items.md` | 架构、采购、WBS、实现 | P1 输出直接驱动下游 |
| `docs/02_architecture/*` | `docs/04_deployment/*`、`src/`、`firmware/`、`hardware/`、`config/`、`scripts/` | 架构约束实现 |
| `README.md` | 仓库入口 | 只做摘要，不定义设计事实 |
| `CHANGELOG.md` | 版本记录 | 只记变化，不定义方案 |
| `docs/DOC_INDEX.md` | 索引导航 | 只描述关系，不生成事实 |

补充说明：`file_structure_design_proposal.md` 只能作为规划方案参考，不能当作当前真实目录树。

---

## 4. 修改某类内容时应同步检查哪些文件

| 变更内容 | 应同步检查 |
| --- | --- |
| 修改定义层 | 相关定义文件、`iter1_function_items.md`、`iter1_function_list.md`、`project_workflow.md`、相关 DEC、必要时同步 `README.md` |
| 修改功能清单或技术选型 | `docs/00_definition/*`、相关 DEC、`system_architecture.md`、`compute_comm_architecture.md`、`hardware_architecture.md`、`software_architecture.md`、`interface_definition.md`、`wbs.md`、`risk_register.md`、`CHANGELOG.md` |
| 修改架构或接口 | `system_architecture.md`、`compute_comm_architecture.md`、`power_architecture.md`、`hardware_architecture.md`、`software_architecture.md`、`interface_definition.md`、相关 DEC、`iter1_function_list.md` |
| 修改 DEC | 对应的规划、架构、部署和实现文档，以及所有引用该决策的文字 |
| 修改部署 / 实现 / 硬件 / 实验 / 报告内容 | 相关架构文档、`interface_definition.md`、`README.md`、`CHANGELOG.md`，以及后续采购输出 |
| 修改 `README.md` | `docs/DOC_INDEX.md`、当前阶段相关文档、必要时 `CHANGELOG.md` |
| 修改 `CHANGELOG.md` | 版本说明相关文档、`README.md`、可能受影响的下游说明 |

---

## 5. 当前占位或低完成度文件

| 文件 | 状态 | 说明 |
| --- | --- | --- |
| `docs/01_planning/risk_register.md` | 占位 | 当前只有标题 |
| `docs/01_planning/wbs.md` | 占位 | 当前只有标题 |
| `docs/01_planning/file_structure_design_proposal.md` | 规划方案 | 不是当前真实目录树 |
| `docs/04_deployment/orin_nx_setup.md` | 占位 | 当前只有标题 |
| `docs/04_deployment/ros2_workspace_setup.md` | 占位 | 当前只有标题 |
| `docs/04_deployment/stm32_setup.md` | 占位 | 当前只有标题 |
| `src/README.md` | 占位 | 只是目录说明 |
| `firmware/README.md` | 占位 | 只是目录说明 |
| `hardware/README.md` | 占位 | 只是目录说明 |
| `config/README.md` | 占位 | 只是目录说明 |
| `scripts/README.md` | 占位 | 只是目录说明 |
| `reports/README.md` | 占位 | 只是目录说明 |
| `presentation/README.md` | 占位 | 只是目录说明 |
| `experiments/README.md` | 占位 | 只是目录说明 |
| `simulation/README.md` | 占位 | 只是目录说明 |
| `data/README.md` | 占位 | 只是目录说明 |
| `process/decisions/DEC-000_example.md` | 示例 | 不参与事实裁决 |
| `process/decisions/DEC-009-semantic_location_owned_by_ap_manager.md` | 空文件 | 待补齐与确认 |
| `process/decisions/DEC-013-manual_takeover_and_estop.md` | 废弃 | 已废弃，不再作为人工接管、急停或电源架构事实源 |
| `process/decisions/DEC-014-power_architecture_boundary.md` | 有效 | 电源架构主边界事实源 |
| `docs/_meta/` | 已建立治理元数据目录 | `conventions/` 已包含 `ai_workflow.md` 与 `document_governance.md`；`audit/` 已包含 G0 已有文件审计报告；`templates/` 可作为后续模板目录使用 |
| `process/change_requests/` | 已建立最小 CR 机制 | 包含 `README.md`、`CR-000_template.md` 以及 `CR-001` 至 `CR-008` 等变更记录 |

---

## 6. 跨文件修改前必看文件与流程

跨文件修改前，先看这些文件：
1. `AGENTS.md`
2. `docs/DOC_INDEX.md`
3. `docs/_meta/conventions/ai_workflow.md`
4. `docs/_meta/conventions/document_governance.md`
5. 相关 `process/change_requests/*`
6. 相关 `docs/00_definition/*`
7. 相关 `process/decisions/*`
8. `docs/01_planning/iter1_function_list.md`
9. `docs/01_planning/iter1_function_items.md`
10. 相关 `docs/02_architecture/*`，尤其是 `interface_definition.md`
11. 若涉及硬件或采购，再看 `hardware/` 与 `docs/04_deployment/`
12. 若涉及对外摘要或版本说明，再看 `README.md` 与 `CHANGELOG.md`

跨文件修改统一遵循：

| 步骤 | 要求 |
| --- | --- |
| Plan | 只读分析，列出影响范围和文件清单 |
| Execute | 只修改批准清单中的文件 |
| Verify | 检查事实一致性、引用关系、命名和边界 |
| Commit | 人工查看 diff 后再提交到 Git |

---

## 7. 当前治理状态与后续待办

1. G0 核心治理收束已完成，G0 已有文件审计报告保留为后续复核依据；
2. 后续跨文件治理修改继续使用 `process/change_requests/` 管理；
3. 对需要人工确认的 DEC 异常保持只读复核，不在索引中替 DEC 下结论；
4. 当前主线回到 P1.3，后续再按批准范围推进 `procurement_list.md` 与 `hardware/bom.csv`。
