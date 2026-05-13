# CR-009：迭代二演进边界口径调整

## CR 编号

CR-009

## 标题

迭代二演进边界口径调整

## 状态

草案

## 日期

2026-05-11

## 发起原因

当前多个文件中仍承接“迭代二在既有骨架上做增量增强，不推翻重来”的旧口径。

该口径在早期阶段用于防止迭代二无边界推翻项目路线，但目前需要调整为更准确的表述：

> 不无理由推翻已验收平台基线，但研究增强模块可在 DEC / CR 支撑下替换、重构或并行实验。

本次调整不是允许无边界重写项目，也不是削弱迭代一平台基线、安全边界、基础导航链路和任务执行闭环，而是避免“迭代二只能在旧骨架上增量叠加”的表述限制后续研究增强模块的合理演进。

## 变更目标

1. 将“迭代二不推翻重来 / 只做增量增强”的绝对表述，调整为“保护已验收平台基线，同时允许研究增强模块在 DEC / CR 支撑下替换、重构或并行实验”。
2. 保留迭代一已验收平台基线、安全边界、基础导航链路和任务执行闭环不能被无理由破坏的约束。
3. 只处理直接承接该旧口径的文件，不借机重写无关文档。
4. 修改 DEC 结论或关键表述前，必须经过人工确认。
5. 不修改硬件架构边界，不进入 BOM、采购清单或实现层代码。
6. 为后续 C-04、C-05、C-06、C-07、C-08、C-09 的具体修改提供统一 CR 边界。
7. 将 C-10 作为本 CR 的排除边界和验证边界，明确 `docs/02_architecture/hardware_architecture.md` 不纳入本轮修改。

## 待确认新口径草案

本 CR 拟确认的新口径如下，后续是否进入正式文件修改，仍需人工确认：

> 迭代二原则上继承迭代一已验收的平台基线和工程骨架，避免无理由推翻重来；但对于语义导航、开放集感知、任务策略、上层算法和研究增强模块，可在明确 CR / DEC 支撑、影响范围评估和回滚边界的前提下，允许替换、重构、并行实验或新增路线。此类变更不得削弱底盘安全、人工接管、急停、系统模式仲裁、电源边界、通信主链路和已验收平台基线。

该口径是待确认草案，不表示相关 DEC、规划层或 Architecture 文件已经完成修改，也不表示允许无边界重构、推翻平台基线或跳过 CR / DEC 流程。

## 初步影响范围

本 CR 创建阶段只创建本 CR 文件。

后续 Plan 阶段需要只读复核：

1. `process/decisions/DEC-001-iteration_roadmap_no_rewrite.md`
2. `process/decisions/DEC-005-*`
3. `docs/01_planning/iter1_function_list.md`
4. `docs/02_architecture/software_architecture.md`
5. 其他可能直接出现以下旧口径的文件：
   - “不推翻重来”
   - “增量增强”
   - “不推翻软件架构”
   - “既有骨架上增强”
   - “只在既有系统总架构、软件架构和接口骨架上增强能力”

后续 Execute 阶段是否允许修改上述文件，必须在 Plan 阶段完成只读检索和人工确认后再决定。

## Plan 阶段只读检查结果

本轮只读检查结论如下：

1. CR-009 适合承接 C-04、C-05、C-06、C-07、C-08、C-09。
2. C-10 应作为本 CR 的排除边界和验证边界：`docs/02_architecture/hardware_architecture.md` 不纳入本轮修改。
3. CR-009 不应混入以下问题：
   - C-01 至 C-03：治理规则与入口文件泛化；
   - C-11：无效 AI citation / 孤立数字残留；
   - C-12 至 C-14：DOC_INDEX 定位和分类修正；
   - C-15：DEC 格式统一；
   - C-16：DEC-009 补全；
   - C-17：AGENTS 当前优先级；
   - C-18：CHANGELOG 发布节奏；
   - C-19 至 C-22：作者名、格式、结构整理；
   - C-23：CR README 泛化；
   - C-24：同步型文件影响检查。
4. 当前 CR-009 仍为草案；后续修改 DEC、Planning 或 Architecture 前，必须完成影响范围确认并获得人工批准。
5. 本轮只读检索发现，除主要候选文件外，部分 DEC、系统架构和计算通信架构文件也存在相关旧口径，需要作为候选影响范围记录，但不自动批准修改。

## 影响范围初步清单

### A. 主要候选修改文件

后续 Execute 阶段如经人工批准，主要候选修改文件包括：

1. `process/decisions/DEC-001-iteration_roadmap_no_rewrite.md`
2. `process/decisions/DEC-005-*`
3. `docs/01_planning/iter1_function_list.md`
4. `docs/02_architecture/software_architecture.md`

### B. 仅作为候选影响范围、需人工确认是否纳入

以下文件只作为候选影响范围记录，是否进入后续 Execute 必须由人工单独确认：

1. `process/decisions/DEC-002-*`
2. `process/decisions/DEC-004-*`
3. `process/decisions/DEC-006-*`
4. `docs/02_architecture/system_architecture.md`
5. `docs/02_architecture/compute_comm_architecture.md`
6. 其他关键词命中的规划、架构、索引或变更记录文件。

### C. 同步型文件

以下文件仅在实际修改发生后，按影响决定是否同步更新；本 CR 草案补全阶段不修改：

1. `CHANGELOG.md`
2. `docs/DOC_INDEX.md`
3. `README.md`
4. `AGENTS.md`
5. `process/change_requests/README.md`

## 后续 Execute 候选允许修改文件

后续 Execute 阶段的候选允许修改文件，必须在人工确认后从以下范围中选择：

1. `process/decisions/DEC-001-iteration_roadmap_no_rewrite.md`
2. `process/decisions/DEC-005-*`
3. `docs/01_planning/iter1_function_list.md`
4. `docs/02_architecture/software_architecture.md`
5. 经人工确认后纳入的 `docs/02_architecture/system_architecture.md`
6. 经人工确认后纳入的 `docs/02_architecture/compute_comm_architecture.md`
7. 经人工确认后纳入的 DEC-002、DEC-004、DEC-006 相关文件
8. 因实际修改需要同步的治理入口或版本记录文件。

未被人工确认列入 Execute 的文件，即使出现在候选影响范围中，也不得修改。

## 本 CR 创建阶段允许修改的文件

1. `process/change_requests/CR-009_iter2_evolution_boundary_rewording.md`

## 本 CR 创建阶段禁止修改的文件

1. `process/decisions/`
2. `docs/00_definition/`
3. `docs/01_planning/`
4. `docs/02_architecture/`
5. `docs/DOC_INDEX.md`
6. `CHANGELOG.md`
7. `README.md`
8. `AGENTS.md`
9. `hardware/`
10. `src/`
11. `firmware/`
12. `config/`
13. `scripts/`
14. `reports/`
15. `presentation/`
16. `experiments/`
17. `simulation/`
18. `data/`
19. 任何未来目录创建
20. P1.3 BOM 或采购清单

## 明确排除和禁止修改范围

本 CR 后续执行阶段也不应修改以下内容，除非另立 CR 并经人工明确批准：

1. `docs/02_architecture/hardware_architecture.md`
2. `process/decisions/DEC-007-*`
3. `process/decisions/DEC-008-*`
4. `process/decisions/DEC-014-*`
5. `process/decisions/DEC-018-*`
6. `process/decisions/DEC-019-*`
7. 对应安全、人工接管、急停、系统模式仲裁、电源边界 DEC 或事实源
8. `hardware/`
9. `firmware/`
10. `src/`
11. `config/`
12. `scripts/`
13. BOM / 采购 / 部署 / 实现文件

本 CR 的目标是调整迭代二演进边界表述，不处理硬件架构事实、采购事实、实现层代码、部署流程或安全底线事实源。

## 涉及 DEC

本 CR 涉及已确认 DEC 的关键表述调整，尤其是：

1. `DEC-001-iteration_roadmap_no_rewrite.md`
2. `DEC-005-*`

本 CR 创建阶段不修改任何 DEC。

后续如需修改 DEC-001 或 DEC-005 的结论、状态或关键表述，必须先完成只读影响分析，并由人工确认后再进入 Execute。

## DEC-001 修改边界

如后续人工批准修改 `DEC-001-iteration_roadmap_no_rewrite.md`，边界如下：

1. 允许调整“不推翻重来 / 增量增强”的绝对化表达。
2. 不允许推翻迭代一已验收平台基线。
3. 不允许取消迭代一先完成、再进入迭代二的阶段路线。
4. 不允许削弱平台稳定性、可运行性、可回退性和工程闭环要求。
5. 修改目标仅是为迭代二研究增强模块保留受控演进空间。

## DEC-005 修改边界

如后续人工批准修改 `DEC-005-*`，边界如下：

1. 保留迭代一语义导航基线，例如 YAML 语义位置表 + 规则匹配等已确认基础方案。
2. 放宽迭代二研究增强空间。
3. 允许未来在 CR / DEC 支撑下讨论开放集语义导航、语义感知增强、并行实验或替代模块。
4. 不得把开放集方向写成当前已完成能力。
5. 不得把开放集方向写成当前阶段必须实现项。

## Planning 同步边界

如后续人工批准同步 `docs/01_planning/iter1_function_list.md` 等规划层文件，边界如下：

1. 只能同步迭代二演进边界的新口径。
2. 不得重写 P1.3 当前任务。
3. 不得把未来研究增强写成当前阶段义务。
4. 不得扩大当前采购范围、实现范围或 P1.3 交付范围。
5. 不得改变迭代一功能清单和技术选型的已确认事实，除非另有 DEC / CR 支撑。

## Architecture 同步边界

如后续人工批准同步 Architecture 文件，边界如下：

1. `docs/02_architecture/software_architecture.md` 可同步“软件架构演进边界”的新口径。
2. `docs/02_architecture/system_architecture.md` 是否纳入后续修改，需人工确认。
3. `docs/02_architecture/compute_comm_architecture.md` 是否纳入后续修改，需人工确认。
4. 只允许调整演进边界表述。
5. 不得修改实际系统架构。
6. 不得修改通信主链路。
7. 不得修改安全链路。
8. 不得修改电源边界。
9. 不得修改人工接管、急停或系统模式仲裁机制。
10. 不得修改 `docs/02_architecture/hardware_architecture.md`。

## 风险评估

如果不调整该口径，后续迭代二研究增强可能被误读为只能在既有 YAML、规则链路或旧软件骨架上做线性叠加，从而限制语义导航、开放集识别、多模态理解、VLN 等研究增强模块的合理替换、重构或并行实验。

如果调整过度，又可能被误读为允许无边界推翻项目路线，破坏迭代一已验收平台基线、安全边界、基础导航链路和任务执行闭环。

因此本 CR 必须保持两个边界：

1. 不无理由推翻已验收平台基线。
2. 研究增强模块可在 DEC / CR 支撑下替换、重构或并行实验。

## 人工确认点

后续进入 Execute 前，必须由人工确认以下事项：

1. 是否允许修改 `process/decisions/DEC-001-iteration_roadmap_no_rewrite.md`。
2. 是否允许修改 `process/decisions/DEC-005-*`。
3. 是否纳入 `docs/02_architecture/system_architecture.md`。
4. 是否纳入 `docs/02_architecture/compute_comm_architecture.md`。
5. 是否只记录 DEC-002、DEC-004、DEC-006 为候选影响范围，暂不修改。
6. 是否允许同步 `docs/01_planning/iter1_function_list.md`。
7. 是否允许同步 `docs/02_architecture/software_architecture.md`。
8. 是否需要更新 `CHANGELOG.md` 的 Unreleased。
9. 是否需要更新 `docs/DOC_INDEX.md`、`README.md`、`AGENTS.md`。

## 执行计划

1. Plan：只读检索所有直接承接“迭代二不推翻重来 / 增量增强 / 不推翻软件架构”等旧口径的文件，列出影响范围和建议修改清单。
2. 人工确认：确认哪些文件进入本轮 Execute，哪些文件只记录为后续待处理。
3. Execute：仅修改人工批准范围内的文件，只调整相关口径，不重写无关章节。
4. Verify：检查 DEC、规划层、架构层之间的新口径是否一致，确认没有破坏安全边界、人工接管、急停、电源边界、P1.3 主线和已验收平台基线。
5. Commit：人工查看 diff 后再提交，并在必要时更新 CHANGELOG 或 DOC_INDEX。

## 验证方式

后续 Verify 阶段需要执行以下检查：

1. 关键词复检：
   - 迭代二
   - 不推翻
   - 推翻重来
   - 增量增强
   - 既有骨架
   - 平台基线
   - 研究增强
   - 开放集
   - 闭集
   - 语义导航
2. 确认 DEC、Planning、Architecture 中的新口径一致。
3. 确认没有把“允许受控演进”写成“允许无边界重构”。
4. 确认没有削弱安全、人工接管、急停、系统模式仲裁、电源边界。
5. 确认没有修改 `docs/02_architecture/hardware_architecture.md`。
6. 确认没有修改 BOM、采购、源码、固件、部署文件。
7. 确认没有把开放集方向写成当前已完成或当前必须实现。
8. 确认所有 DEC / Architecture 修改都有人工确认。
9. 确认实际 diff 只包含人工批准范围内的文件。

## 验证清单

1. 已完成旧口径只读检索。
2. 已列出所有直接承接旧口径的文件。
3. DEC-001 如被修改，保留已验收平台基线和主链路安全边界。
4. DEC-005 如被修改，不推翻迭代一 YAML 语义位置表 + 规则匹配基线，只放宽迭代二研究增强边界。
5. `iter1_function_list.md` 如被修改，只调整绝对化表述，不重写功能路线。
6. `software_architecture.md` 如被修改，只调整迭代二演进边界，不随意推翻软件架构总骨架。
7. 未修改 `hardware_architecture.md`。
8. 未修改实现层代码。
9. 未创建未来目录。
10. 未创建 P1.3 BOM 或采购清单。
11. git diff 只包含批准范围内文件。

## 发布节奏

1. 本次 CR-009 草案补全本身不发布版本。
2. 后续若执行跨文件修改，可先记录到 `CHANGELOG.md` 的 Unreleased。
3. 是否正式发版由后续治理完成后人工决定。

## 回滚方式

如果本 CR 创建阶段需要回滚，可删除本 CR 文件。

如果后续执行阶段已经提交，可通过 `git revert` 回滚对应 commit。

如果尚未提交，可通过 `git restore` 回滚批准范围内文件。

## 最终结果

待执行后填写。
