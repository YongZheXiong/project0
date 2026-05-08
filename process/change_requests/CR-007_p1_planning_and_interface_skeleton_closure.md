# CR-007：P1 规划与接口骨架收口

## CR 编号

CR-007

## 标题

P1 规划与接口骨架收口

## 状态

草案

## 日期

2026-05-08

## 发起原因

CR-004 审计报告指出，`docs/01_planning/iter1_function_items.md` 存在重复和交叠内容块，尤其是任务调度相关段落，颗粒度不够干净；`docs/02_architecture/interface_definition.md` 仍是骨架版 V0.1，部分接口名称和归属尚未冻结；`process/decisions/DEC-009-semantic_location_owned_by_ap_manager.md` 为空文件，应继续视为异常待复核。上述问题不直接阻塞 P1.3 采购，但会影响 G0 文档规范、后续实现落地和 Agent 理解，因此需要通过 CR-007 分批收口。

## 变更目标

1. 收敛 `iter1_function_items.md` 中重复和交叠的内容块；
2. 保持 P1 功能条目颗粒度清晰，不重写功能路线；
3. 复核 `interface_definition.md` 的骨架状态；
4. 形成一版 P1 接口骨架口径，并对尚未最终冻结的接口命名与归属进行明确标注，尤其是 `QuerySemanticPose/GetSemanticPose`、`TriggerEmergencyStop`、`NavigateToSemantic.action` 等；
5. 只读复核 DEC-009 的空文件状态；
6. 不直接修改已确认 DEC 结论；
7. 不提前展开 P2-P6 实现内容；
8. 为后续 P1.3 和后续实现阶段提供更清楚的规划与接口基线。

## 影响范围

本 CR 创建阶段只创建 CR-007 文件。

后续执行阶段可能修改：

1. `docs/01_planning/iter1_function_items.md`
2. `docs/02_architecture/interface_definition.md`
3. `docs/DOC_INDEX.md`

后续执行阶段可能只读复核：

1. `docs/02_architecture/software_architecture.md`
2. `process/decisions/DEC-009-semantic_location_owned_by_ap_manager.md`

## 允许修改的文件

本 CR 创建阶段只允许创建：

1. `process/change_requests/CR-007_p1_planning_and_interface_skeleton_closure.md`

后续执行阶段可能允许修改：

1. `docs/01_planning/iter1_function_items.md`
2. `docs/02_architecture/interface_definition.md`
3. `docs/DOC_INDEX.md`

## 禁止修改的文件

1. `process/decisions/DEC-013-manual_takeover_and_estop.md`
2. `process/decisions/DEC-014-power_architecture_boundary.md`
3. `process/decisions/DEC-018-manual_takeover_input_scheme.md`
4. `process/decisions/DEC-019-emergency_stop_layout.md`
5. `docs/00_definition/`
6. `docs/02_architecture/system_architecture.md`
7. `docs/02_architecture/compute_comm_architecture.md`
8. `docs/02_architecture/power_architecture.md`
9. `docs/02_architecture/hardware_architecture.md`
10. `hardware/`
11. `src/`
12. `firmware/`
13. `config/`
14. `scripts/`
15. `reports/`
16. `presentation/`
17. `experiments/`
18. `simulation/`
19. `data/`
20. 未来目录创建
21. P1.3 BOM 或采购清单

## 涉及 DEC

1. DEC-009：仅只读复核其空文件 / 异常待复核状态，不在本 CR 创建阶段修改。
2. DEC-013、DEC-014、DEC-018、DEC-019：不得修改其已确认或已废弃结论。

## 风险评估

如果不处理本 CR 涉及问题，`iter1_function_items.md` 的重复和交叠内容会继续影响文档颗粒度和 Agent 理解；`interface_definition.md` 的骨架接口名称和归属如果长期不收口，会影响后续实现落地；DEC-009 为空文件若被误读为有效决策，会影响后续语义位置归属判断。

## 执行计划

1. Plan：只读复核 `iter1_function_items.md`、`interface_definition.md`、`software_architecture.md`、`DOC_INDEX.md` 和 DEC-009；
2. 人工确认：确认本 CR 是否只处理规划与接口骨架，DEC-009 是否继续保持异常待复核；
3. Execute：仅在批准范围内收敛 `iter1_function_items.md` 重复段落，整理 `interface_definition.md` 的接口命名和归属标注，必要时同步 `DOC_INDEX.md`；
4. Verify：检查未修改已确认 DEC，未扩展到 P2-P6，实现内容未被提前补写，diff 只包含批准范围；
5. Commit：人工查看 diff 后提交，并关闭 CR-007。

## 验证清单

1. CR-007 已建立；
2. `iter1_function_items.md` 重复和交叠内容已被识别；
3. `interface_definition.md` 骨架状态已被复核；
4. 接口命名与归属已形成一版清晰口径或明确标注为待冻结；
5. DEC-009 未被误认为有效事实源；
6. 未修改 DEC-013、DEC-014、DEC-018、DEC-019 等已确认结论；
7. 未创建未来目录；
8. 未进入 P1.3 BOM 或采购清单；
9. 未展开 P2-P6 或 P7-P10；
10. git diff 只包含批准范围内文件。
11. 如本 CR 仅标注接口骨架状态与待冻结项，不修改 CHANGELOG；如实际变更接口命名或归属结论，则需人工确认是否另开 CR 或扩展本 CR 同步 CHANGELOG。

## 回滚方式

如果 CR-007 创建阶段需要回滚，可删除该 CR 文件；如果后续执行阶段已经提交，可通过 `git revert` 回滚对应 commit；如果尚未提交，可通过 `git restore` 回滚批准范围内文件。

## 最终结果

待填写。

## 关联 commit

未提交。
