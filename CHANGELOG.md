# Changelog

All notable changes to Project-0 will be documented in this file.

## [Unreleased]

### Changed
- 按 CR-010 泛化治理入口文件说明，新增 G0 governance baseline closure 历史说明入口。
- 轻量同步 `AGENTS.md` 中的 G0 历史说明入口，并记录 CR 机制和文档索引相关治理说明更新。

---

## [0.1.0] - 2026-4-17

### Added
- 初始化Project0的仓库
- 建立了文档结构
- 新增了 iter1_core_capabilities.md
- 新增了 iter2_enhancement_scope.md
- 新增了 milestone_timeline.md
- 新增了 objective_constraints.md
- 新增了 overall_deliverables.md
- 新增了 project_workflow.md
- 新增了 subjective_requirements.md
- 新增了 system_positioning.md
- 新增了 version_roadmap.md

---

## [0.2.0] - 2026-4-17

### Added
- 新增了 iter1_function_list.md
- 新增了 system_architecture.md
- 新增了 compute_comm_architecture.md
- 新增了 software_architecture.md

---

## [0.2.1] - 2026-4-20

### Added
- 新增了 power_architecture.md
- 新增了 电源构架的一系列决策记录文件
- 新增了 hardware_architecture.md
- 新增了 硬件架构的一系列决策记录文件

### Changed
- 统一了 决策文件的命名标准

---

## [0.2.2] - 2026-4-21

### Added
- 新增了 file_structure_design_proposal.md
- 新增了 interface_definition.md
- 新增了 ros2_package_topic_service_action.md

### Changed
- 重构并重写了software_architecture.md

---

## [0.2.3] - 2026-4-24

### Changed
- 更新了 objective_constraints.md 中的已有硬件条件
- 完善了 subjective_requirements.md 的文件格式
- 完善了 iter1_core_capabilities.md 的文件格式
- 完善了 iter2_enhancement_scope.md 的文件格式
- 完善 file_structure_design_proposal.md 的文件格式 
- 完善 iter1_function_list.md 的文件格式
- 更新 power_architecture.md
- 更新 hardware_architecture.md
- 完善 interface_definition.md 文件格式

---

## [0.2.4] - 2026-5-6

### Added
- 新增了 vehicle_hardware_topology.drawio

### Changed
- 统一了 决策文件的格式
- 更改了 hardware_architecture.md 中有关硬件架构的决策
- 重写了 hardware_architecture.md

---

## [0.2.5] - 2026-05-13

### Added
- 新增 `docs/DOC_INDEX.md` 作为文档索引与依赖导航入口。
- 新增 `process/change_requests/` 变更请求机制，用于管理跨文件修改。
- 新增 `docs/_meta/conventions/ai_workflow.md` 与 `docs/_meta/conventions/document_governance.md`，用于约束 AI 工作流和文档治理规则。

### Changed
- 发布版本 `v0.2.5`，G0 正式收束。
- G0 已达到可收束的最小治理基线，当前主线回到 P1.3 硬件方案与采购。
- 明确 G0 结束不等于所有遗留问题清零，遗留问题后续按现有 CR / 阶段任务机制承接，不新增专门的后续治理跟踪文件。
- README 已对齐 G0 正式收束状态和文档导航。
- DEC-013 已废弃，人工接管链路已按 DEC-018 对齐。
- `AGENTS.md`、`docs/DOC_INDEX.md`、`README.md`、`CHANGELOG.md` 已按 CR-003 对齐治理入口。
- 按 CR-004 完成全项目已有文件只读审计，并输出 G0 已有文件审计报告。
- 按 CR-005 统一 P1.3 硬件命名基线。
- 按 CR-006 修正 `file_structure_design_proposal.md` 定性，明确其不是当前真实目录树。
- 按 CR-007 收口 P1 规划与接口骨架状态。
- 按 CR-008 完成最终治理文档状态收尾，当前主线回到 P1.3 硬件方案与采购。
- 本版本不修改 DEC，不修改 Architecture 技术事实，不做硬件采购决策，不输出 BOM 或采购清单。

