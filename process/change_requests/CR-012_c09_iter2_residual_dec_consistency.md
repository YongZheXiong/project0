# CR-012: C-09 迭代二旧口径残留 DEC 一致性审查

## 状态

已完成

## 背景

CR-009 已完成并收束，已将迭代二演进边界调整为：

> 保护已验收平台基线，同时允许语义导航、开放集感知、任务策略、上层算法和研究增强模块在明确 CR / DEC 支撑、影响范围评估和回滚边界下受控演进。

C-09 只读复检发现 DEC-004 和 DEC-006 仍存在偏绝对的旧口径残留。

本 CR 用于审查并在必要时修正 DEC-004 / DEC-006 与 CR-009 新口径之间的局部张力。

## 覆盖问题

1. C-09：CR-009 旧口径残留复检。
2. 重点候选：
   - `process/decisions/DEC-004-navigation_nav2_navfn_rpp.md`
   - `process/decisions/DEC-006-task_manager_behaviortree_cpp.md`

## 只读复检结论

1. `docs/02_architecture/system_architecture.md`：无命中，不处理。
2. `docs/02_architecture/compute_comm_architecture.md`：不处理；“不推翻主从骨架”属于通信主链路和平台基线保护。
3. `process/decisions/DEC-002-base_communication_uart_binary_protocol.md`：不处理；“底层通信方案不变”属于通信主链路保护。
4. `process/decisions/DEC-004-navigation_nav2_navfn_rpp.md`：存在可能需要同步的新口径残留，需 DEC 一致性审查。
5. `process/decisions/DEC-006-task_manager_behaviortree_cpp.md`：存在可能需要同步的新口径残留，需 DEC 一致性审查。

## 建议修改范围

后续如 Execute，候选白名单仅限：

1. `process/decisions/DEC-004-navigation_nav2_navfn_rpp.md`
2. `process/decisions/DEC-006-task_manager_behaviortree_cpp.md`
3. `process/change_requests/CR-012_c09_iter2_residual_dec_consistency.md`

## 明确排除范围

1. 不修改 `docs/02_architecture/compute_comm_architecture.md`。
2. 不修改 `process/decisions/DEC-002-base_communication_uart_binary_protocol.md`。
3. 不修改 `docs/02_architecture/system_architecture.md`。
4. 不修改硬件架构、硬件、BOM、采购。
5. 不修改源码、固件、Docker、服务、构建、部署。
6. 不削弱安全、急停、人工接管、系统模式仲裁、电源边界、通信主链路。
7. 不把未来研究增强写成当前已完成。
8. 不把未来研究增强写成当前阶段义务。
9. 不做无边界重构。
10. 不推翻已验收平台基线。

## 执行原则

1. 本 CR 不直接推翻 DEC-004 或 DEC-006。
2. 后续如修改 DEC-004 / DEC-006，只允许调整绝对化措辞，使其与 CR-009 新口径一致。
3. 保留迭代一基线选择：
   - DEC-004 中 Nav2 / NavFn / RPP 作为迭代一基线。
   - DEC-006 中 BehaviorTree.CPP 作为迭代一任务管理基线。
4. 后续研究增强如果超出插件、节点或 XML 级增强，必须通过 CR / DEC、影响范围评估和回滚边界确认。
5. 不削弱安全、急停、人工接管、系统模式仲裁、电源边界、通信主链路。

## 风险

1. 误将未来研究增强写成当前阶段义务。
2. 误削弱迭代一已验收平台基线。
3. 误把 DEC-004 / DEC-006 改成允许无边界重构。
4. 误触碰通信主链路、安全、急停、人工接管或系统模式仲裁边界。

## 验证方式

1. `git status --short`
2. `git diff --name-only`
3. `git diff --check`
4. 检查是否只修改批准文件。
5. 检查 DEC-004 / DEC-006 是否仍保留迭代一基线事实。
6. 检查是否未修改 DEC-002、`docs/02_architecture/compute_comm_architecture.md`、`docs/02_architecture/system_architecture.md`。
7. 检查是否未修改硬件、BOM、采购、源码、固件、Docker、服务、构建、部署相关文件。

## 当前结果

CR-012 草案已创建并提交：

1. `9f7b7b8360aed851ba5ec26f4b10f30e3b9d44e8`
   `docs(cr): add CR-012 C-09 DEC consistency draft`

CR-012 DEC-004 / DEC-006 一致性修正已完成并提交：

1. `8d7c9a7077979e87357001a9d308779a0c49b35f`
   `docs(cr-012): align DEC-004 and DEC-006 evolution wording`

实际修改文件：

1. `process/decisions/DEC-004-navigation_nav2_navfn_rpp.md`
2. `process/decisions/DEC-006-task_manager_behaviortree_cpp.md`

DEC-004 已完成：

1. 将“Nav2 不变 / 不更换导航框架 / 不推翻重来”等绝对化旧口径，调整为“保留 Nav2 / NavFn / RPP 迭代一基线 + 后续研究增强需 CR / DEC、影响范围评估和回滚边界确认”的受控演进口径。

DEC-006 已完成：

1. 将“只扩展 BT 节点和 XML / 不需要推翻重来”等绝对化旧口径，调整为“保留 BehaviorTree.CPP 迭代一任务管理基线 + 后续任务策略、任务组织层或并行实验需 CR / DEC、影响范围评估和回滚边界确认”的受控演进口径。

明确未改变：

1. DEC-004 的 Nav2 / NavFn / RPP 迭代一导航基线。
2. DEC-006 的 BehaviorTree.CPP 迭代一任务管理基线。
3. DEC 状态、日期、标题、替代关系或核心决策结论。
4. 安全、急停、人工接管、系统模式仲裁、电源边界、通信主链路。

明确未修改：

1. `process/decisions/DEC-001-iteration_roadmap_no_rewrite.md`
2. `process/decisions/DEC-002-base_communication_uart_binary_protocol.md`
3. `docs/02_architecture/system_architecture.md`
4. `docs/02_architecture/compute_comm_architecture.md`
5. `README.md`
6. `docs/DOC_INDEX.md`
7. `AGENTS.md`
8. `CHANGELOG.md`
9. 硬件、BOM、采购、源码、固件、Docker、服务、构建、部署相关文件。

C-09 当前状态：

1. C-09 中本轮确认需要处理的 DEC-004 / DEC-006 旧口径残留已完成。
2. `docs/02_architecture/system_architecture.md` 无命中。
3. `docs/02_architecture/compute_comm_architecture.md` 与 `process/decisions/DEC-002-base_communication_uart_binary_protocol.md` 属于通信主链路保护，不纳入修改。
