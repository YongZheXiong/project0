# CR-001

## 标题

DEC 异常复核与人工接管链路对齐

## 状态

已完成

## 日期

2026-05-08

## 发起原因

当前 DEC 层存在异常：DEC-009 为空文件，DEC-013 文件名与正文主题不一致，DEC-013 与 DEC-014 内容高度重复。同时，人工接管链路在 DEC-018 / hardware_architecture.md 与 compute_comm_architecture.md / power_architecture.md 之间存在不一致，可能影响 P1.3 BOM 与采购清单。

## 变更目标

1. 记录 DEC 异常复核结果；
2. 明确 DEC-009 暂缓处理；
3. 明确 DEC-014 拟作为电源架构主边界事实源；
4. 明确 DEC-013 需由人工确认后再处理；
5. 明确人工接管输入方案拟以 DEC-018 为事实源；
6. 后续在人工批准后修复 compute_comm_architecture.md 与 power_architecture.md 中的下游冲突；
7. 为 P1.3 procurement_list.md 与 hardware/bom.csv 清理前置事实冲突。

## 影响范围

本 CR 创建阶段不修改受影响文件，仅记录后续可能影响范围。

可能受影响的文件：

- process/decisions/DEC-013-manual_takeover_and_estop.md
- docs/02_architecture/compute_comm_architecture.md
- docs/02_architecture/power_architecture.md
- docs/02_architecture/hardware_architecture.md
- docs/01_planning/procurement_list.md
- hardware/bom.csv

## 允许修改的文件

本 CR 创建阶段只允许创建：

- process/change_requests/CR-001_dec_anomaly_and_manual_takeover_alignment.md

后续执行阶段可能允许修改：

- process/decisions/DEC-013-manual_takeover_and_estop.md
- docs/02_architecture/compute_comm_architecture.md
- docs/02_architecture/power_architecture.md

必要时只读检查：

- docs/02_architecture/hardware_architecture.md

## 禁止修改的文件

- process/decisions/DEC-009-semantic_location_owned_by_ap_manager.md
- process/decisions/DEC-014-power_architecture_boundary.md
- process/decisions/DEC-018-manual_takeover_input_scheme.md
- process/decisions/DEC-019-emergency_stop_layout.md
- docs/00_definition/
- docs/01_planning/iter1_function_list.md
- docs/01_planning/iter1_function_items.md

## 涉及 DEC

- DEC-009
- DEC-013
- DEC-014
- DEC-018
- DEC-019

## 风险评估

如不处理，DEC-013 可能被误认为人工接管 / 急停事实源，DEC-014 的电源边界事实源地位可能不清晰，DEC-018 的人工接管输入方案可能被下游文档冲突削弱，DEC-019 的急停边界也可能在供电与通信链路中被误读。上述问题会直接影响人工接管、电源边界、急停边界，以及 P1.3 BOM 与采购清单的准确性。

## 执行计划

1. 人工确认本 CR；
2. 修改 DEC-013 的状态或说明，但不改变 DEC-014、DEC-018、DEC-019 结论；
3. 按 DEC-018 修复 compute_comm_architecture.md 与 power_architecture.md 的人工接管下游表述。

## 验证清单

- DEC-013 不再被误认为人工接管 / 急停事实源；
- DEC-014 保持电源边界事实源；
- DEC-018 保持人工接管输入方案事实源；
- compute_comm_architecture.md 不再写传统遥控接收机进入 STM32 作为当前方案；
- power_architecture.md 不再把传统遥控接收机作为当前必须供电对象；
- hardware_architecture.md 与 DEC-018 保持一致；
- git diff 只包含批准范围内文件。

## 回滚方式

本 CR 创建阶段如需回滚，可通过 git restore 删除本文件变更。后续执行阶段如已提交，可通过 git revert 回滚对应提交；如尚未提交，可通过 git restore 回滚批准范围内的修改文件。

## 最终结果

本 CR 已完成，实际结果如下：

1. DEC-013 已标记为废弃。
2. DEC-013 不再作为人工接管、急停、电源架构事实源。
3. 人工接管事实源以 DEC-018 为准。
4. 急停事实源以 DEC-019 为准。
5. 电源架构主边界以 DEC-014 为准。
6. compute_comm_architecture.md 与 power_architecture.md 已按 DEC-018 修复人工接管链路。
7. 未修改 DEC-014、DEC-018、DEC-019。

## 关联 commit

- a7eb6eb docs(dec): deprecate invalid DEC-013 record
- 048b0de docs(arch): align manual takeover chain with DEC-018
