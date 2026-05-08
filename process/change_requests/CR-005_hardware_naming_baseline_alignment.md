# CR-005：P1.3 硬件命名基线统一

## CR 编号

CR-005

## 标题

P1.3 硬件命名基线统一

## 状态

已完成

## 日期

2026-05-08

## 发起原因

CR-004 审计报告指出，当前仓库中存在硬件命名不统一问题，包括 JGB-520 / GB37-520、Livox Mid360 / Mid-360、D435 / D435i 等。该问题会直接影响 P1.3 BOM、采购清单、接线图、硬件标注和后续 Agent 判断，因此必须在进入 P1.3 采购清单与 BOM 之前先统一硬件命名基线。

## 变更目标

1. 在人工确认后统一 P1.3 前关键硬件 canonical name；
2. 明确 D435 / D435i 的当前项目口径；
3. 明确 Livox Mid360 / Mid-360 的统一写法；
4. 明确 JGB-520 / GB37-520 的统一写法；
5. 保持飞智黑武士2 + 2.4G USB 接收器链路不变；
6. 不修改 DEC 结论；
7. 不改变人工接管链路、急停边界和电源边界；
8. 为后续 P1.3 采购相关文档提供命名基线。

## 影响范围

本 CR 用于约束后续 Agent 按批准范围执行命名统一，当前不进入实际文件修改。

后续执行阶段可能修改：

- `README.md`
- `docs/01_planning/iter1_function_list.md`
- `docs/01_planning/iter1_function_items.md`
- `docs/02_architecture/system_architecture.md`
- `docs/02_architecture/compute_comm_architecture.md`
- `docs/02_architecture/power_architecture.md`
- `docs/02_architecture/hardware_architecture.md`
- `docs/02_architecture/interface_definition.md`
- `docs/02_architecture/diagrams/vehicle_hardware_topology.drawio`

## 允许修改的文件

当前整理/立项阶段只允许修改：

- `process/change_requests/CR-005_hardware_naming_baseline_alignment.md`

后续执行阶段可能允许修改：

- `README.md`
- `docs/01_planning/iter1_function_list.md`
- `docs/01_planning/iter1_function_items.md`
- `docs/02_architecture/system_architecture.md`
- `docs/02_architecture/compute_comm_architecture.md`
- `docs/02_architecture/power_architecture.md`
- `docs/02_architecture/hardware_architecture.md`
- `docs/02_architecture/interface_definition.md`
- `docs/02_architecture/diagrams/vehicle_hardware_topology.drawio`

## 禁止修改的文件

- `process/decisions/`
- `docs/00_definition/`
- `docs/_meta/conventions/`
- `docs/_meta/audit/`
- `process/change_requests/README.md`
- `process/change_requests/CR-000_template.md`
- `process/change_requests/CR-001_dec_anomaly_and_manual_takeover_alignment.md`
- `process/change_requests/CR-002_ai_workflow_and_document_governance.md`
- `process/change_requests/CR-003_governance_entry_files_alignment.md`
- `process/change_requests/CR-004_existing_files_audit_and_classification.md`
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
- 任何其他文件

## 涉及 DEC

不直接修改 DEC。CR-005 只统一下游文档中的硬件命名，不改变已确认 DEC 结论。

## 风险评估

如果不统一硬件命名，P1.3 BOM、采购清单、接线图、硬件照片索引和后续 Agent 判断会继续受到命名漂移影响，可能导致采购错误、重复采购、接线图标注混乱或后续文档各写各的名字。

## 执行计划

1. Plan：Agent 只读统计命名漂移，列出出现位置、影响范围和建议 canonical name，不修改文件；
2. 人工确认：由人工确认 D435 / D435i、Livox Mid360 / Mid-360、JGB-520 / GB37-520 的最终 canonical name；
3. Execute：Agent 只修改人工批准范围内的文件，只做硬件命名统一和必要上下文小修；
4. Verify：检查残留命名、越界修改、DEC 未修改、人工接管 / 急停 / 电源边界未改变；
5. Commit：人工查看 diff 后提交，并关闭 CR-005。

## 人工确认点

1. D435 / D435i 的当前项目口径；
2. Livox Mid360 / Mid-360 的统一写法；
3. JGB-520 / GB37-520 的统一写法；
4. 是否需要保留某些未来增强语境中的非当前硬件写法；
5. 上述 canonical name 由人工最终确认，Agent 只按确认结果执行。

## 验证清单

1. D435 / D435i 口径已确认；
2. Livox Mid360 / Mid-360 口径已确认；
3. JGB-520 / GB37-520 口径已确认；
4. 飞智黑武士2 + 2.4G USB 接收器链路保持不变；
5. 人工接管链路保持 DEC-018 路线；
6. 急停边界保持既有硬件急停路线；
7. 电源边界保持 DEC-014 路线；
8. 未修改任何 DEC；
9. 未创建 BOM 或采购清单；
10. 未扩展到 P2-P6 或 P7-P10；
11. git diff 只包含批准范围内文件。

## 回滚方式

如果仅回滚本次立项文件，删除 `process/change_requests/CR-005_hardware_naming_baseline_alignment.md` 即可；如果后续执行阶段产生实际文档修改，则按对应后续 CR 或 commit 逐项回滚。

## 最终结果

CR-005 已完成，实际结果如下：

1. 已统一 P1.3 前关键硬件命名基线；
2. 深度相机统一为 `Intel RealSense D435`，简称 `D435`；
3. 激光雷达统一为 `Livox Mid360`，简称 `Mid360`；
4. 电机统一为 `JGB-520`；
5. 人工接管设备统一为 `飞智黑武士2手柄 + 2.4G USB 接收器`；
6. 已修正 `D435i`、`Livox Mid-360`、`Livox Mid3360`、`GB37-520`、`RealSence D435`、`2.4G USB接收器` 等命名漂移或拼写问题；
7. 未修改任何 DEC 文件；
8. 未改变人工接管链路、急停边界和电源边界；
9. 未创建 BOM 或采购清单；
10. 本 CR 为后续 P1.3 `procurement_list.md` 与 `hardware/bom.csv` 提供硬件命名基线。

## 关联 commit

- 35e46c8 docs(hardware): align P1.3 hardware naming baseline
