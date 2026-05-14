# Changelog

All notable changes to Project-0 will be documented in this file.

## [Unreleased]

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

## [0.2.6] - 2026-05-14

### Added
- 按 CR-010 新增 `docs/_meta/governance/G0_governance_baseline_closure.md`，作为 G0 治理基线收束的历史说明入口。
- 按 CR-013 新建 `DEC-022-semantic_location_ownership_boundary.md` 作为 DEC-009 的替代 DEC 草案，并在后续按 CR-014 转为确认。
- 按 CR-016 新增 `docs/_meta/conventions/ai_collaboration_rules.md`，用于承载长期 AI 协作规则。

### Changed
- 按 CR-009 调整迭代二演进边界口径：保护已验收平台基线，同时允许研究增强模块在 CR / DEC 支撑下受控演进。
- 按 CR-009 同步更新 `DEC-001`、`DEC-005`、`iter1_function_list.md` 和 `software_architecture.md` 中的相关绝对化旧口径。
- 按 CR-010 泛化治理入口与规则文件定位，压缩 G0 阶段性表述，并将文档索引与 CR 机制说明收敛为全阶段口径。
- 按 CR-011 完成一批文档卫生与格式整理，包括作者英文名统一、定义层文档 Markdown 结构规范化，以及残留 citation marker 清理。
- 按 CR-012 修正 `DEC-004` 与 `DEC-006` 中迭代二旧口径残留，使其与 CR-009 的受控演进口径一致。
- 按 CR-013 将 `DEC-009` 从空文件治理为“异常占位 / 非有效事实源”，保留历史编号与追溯关系。
- 按 CR-014 确认 `DEC-022`：语义位置表、语义位置数据与语义查询能力归属 `p0_map_manager`，`p0_semantic_nav` 通过查询接口获取位姿或区域，且不推翻 `DEC-005`。
- 按 CR-015 统一部分 DEC 文件的元信息字段、日期展示和正文结构格式，不改变技术结论、状态含义或替代关系。
- 按 CR-016 拆分 AI 协作规则与操作工作流，收窄 `ai_workflow.md` 职责，并同步 `AGENTS.md`、`README.md`、`docs/DOC_INDEX.md` 等入口引用。
