# CR-010: 治理规则与入口文件泛化

## 状态

已完成

## 背景

G0 已收束，v0.2.5 已发布，项目主线回到 P1.3。下一轮治理发现，部分治理入口和规则文件仍带有 G0 或当前阶段的临时表述，可能误导后续 Agent 和人工执行。

本 CR 用于把治理入口文件从阶段性语境中泛化为全阶段适用的治理入口，同时把 G0 专属历史背景收口到独立说明文件中。

## 目标

1. 明确 G0 是治理基线收束工作包 / 历史说明，不是 P0-P10 的正式阶段。
2. 泛化治理入口与治理规则文件，避免 G0 阶段污染。
3. 修正 DOC_INDEX.md 中治理目录和 CR 目录的分类错误。
4. 将 DOC_INDEX.md 定位为 Project0 全阶段文档索引与依赖关系说明文件，当前版本重点服务 P1.3。
5. 压缩 DOC_INDEX.md 中过重的当前治理状态与后续待办。
6. 将 process/change_requests/README.md 从“当前阶段用途”泛化为全阶段 CR 机制说明。
7. 明确治理同步文件的检查规则。
8. 为后续是否更新 AGENTS.md、README.md、CHANGELOG.md 留出人工确认边界。

## 纳入问题

本 CR 建议纳入：

- C-01：补充 G0 定义 / 确立说明文件
- C-02：ai_workflow.md 命名与内容定位不匹配
- C-03：document_governance.md 中 G0 专章阶段污染
- C-12：DOC_INDEX.md 中“当前占位或低完成度文件”分类错误
- C-13：DOC_INDEX.md 定位应泛化为全阶段文档索引
- C-14：压缩 / 改写 DOC_INDEX.md 中“当前治理状态与后续待办”
- C-23：process/change_requests/README.md 中“当前阶段用途”表述调整
- C-24：治理同步文件随实际修改同步更新

条件纳入：

- C-17：AGENTS.md 中“当前优先级”小节更新，仅在后续人工确认后纳入 Execute。

## 建议后续修改文件

后续候选修改文件包括：

1. docs/_meta/conventions/ai_workflow.md
2. docs/_meta/conventions/document_governance.md
3. docs/DOC_INDEX.md
4. process/change_requests/README.md
5. docs/_meta/governance/G0_governance_baseline_closure.md

条件同步文件：

1. AGENTS.md
2. README.md
3. CHANGELOG.md

## 本 CR 当前不允许直接修改的文件

除非后续人工明确批准，本 CR 不允许修改：

1. AGENTS.md
2. README.md
3. CHANGELOG.md
4. 任何 DEC 文件
5. docs/00_definition/*
6. docs/01_planning/*
7. docs/02_architecture/*
8. docs/04_deployment/*
9. hardware/*
10. firmware/*
11. src/*
12. config/*
13. scripts/*
14. reports/*
15. presentation/*
16. experiments/*
17. simulation/*
18. data/*

## 执行原则

1. 先创建 CR-010 草案。
2. 后续修改必须继续遵守 Plan → Execute → Verify → Commit。
3. Execute 只能修改人工批准的文件清单。
4. 不把 G0 写成 P0-P10 的正式阶段。
5. 不把 DOC_INDEX.md 写成事实源、待办清单或阶段执行计划。
6. 不把 AGENTS.md 写成过重的当前治理任务清单。
7. 不修改技术事实、架构事实、规划事实或硬件事实。
8. 不触碰 BOM、采购、源码、固件、部署、Docker 或服务配置。

## 风险

1. 修改 AGENTS.md 可能影响后续 Agent 行为。
2. 修改 DOC_INDEX.md 可能让索引文件误承担事实源或任务计划职责。
3. 拆分 ai_workflow.md 可能影响现有引用关系。
4. 新增 G0 说明文件时，若表述不严谨，可能把 G0 误写成 P0-P10 正式阶段。
5. 入口文件互相引用，存在范围膨胀风险。
6. CHANGELOG.md 是否需要同步，应在实际修改发生后再判断。

## 初步执行计划

### Plan

只读复核以下文件：

- AGENTS.md
- README.md
- CHANGELOG.md
- docs/DOC_INDEX.md
- docs/_meta/conventions/ai_workflow.md
- docs/_meta/conventions/document_governance.md
- process/change_requests/README.md

输出每个文件是否应修改、建议修改方向、是否需要同步引用。

### Execute

仅在人工确认后，按批准文件白名单分批修改。

第一批候选方向：

1. 新增 docs/_meta/governance/G0_governance_baseline_closure.md
2. 泛化 docs/_meta/conventions/document_governance.md 的 G0 专章
3. 修正 docs/DOC_INDEX.md 的定位和分类
4. 泛化 process/change_requests/README.md 的阶段用途表述
5. 评估 ai_workflow.md 是否拆分为 ai_collaboration_rules.md + 操作化 ai_workflow.md

### Verify

检查：

1. 是否只修改批准文件。
2. 是否未修改 DEC / Architecture / Planning 技术事实。
3. 是否未修改硬件、采购、BOM、源码、固件、部署文件。
4. 是否未把 G0 写成 P0-P10 正式阶段。
5. 是否未让 DOC_INDEX.md 承担过多待办或事实源职责。
6. 是否所有新增 / 拆分文件都有入口引用策略。

### Commit

人工审查 diff 后再提交。

## 当前结果

CR-010 已完成三次提交：

1. `22c327dae50e351ac3a20513f920b1045f01d2b3`
   `docs(cr): add CR-010 governance entry generalization draft`
2. `f4a1e2f77ecfae289e21120f63829f7bbed568f1`
   `docs(cr-010): generalize governance entry files`
3. `8ce357ad3fa58cf09f7e3a7785be95d27e587690`
   `docs(cr-010): sync agents and changelog governance entries`

已完成项：

1. C-01 已完成：新增 `docs/_meta/governance/G0_governance_baseline_closure.md`，用于承接 G0 治理基线收束的历史说明。
2. C-03 已完成：`docs/_meta/conventions/document_governance.md` 已将 G0 专章泛化为全阶段已有文件规范化收束原则。
3. C-12 已完成：`docs/DOC_INDEX.md` 已修正 `docs/_meta/` 与 `process/change_requests/` 的分类。
4. C-13 已完成：`docs/DOC_INDEX.md` 已定位为 Project0 全阶段文档索引与依赖关系说明文件，当前版本重点服务 P1.3。
5. C-14 已完成：`docs/DOC_INDEX.md` 当前治理状态已压缩为摘要，不承担详细任务计划。
6. C-17 已处理：`AGENTS.md` 已轻量同步 G0 历史说明入口和当前主线边界。
7. C-23 已完成：`process/change_requests/README.md` 已泛化为全阶段 CR 机制说明。
8. C-24 已完成：`AGENTS.md`、`CHANGELOG.md`、`docs/DOC_INDEX.md` 等同步文件已按实际修改完成必要同步。

暂缓项：

1. C-02 未完成。
2. `docs/_meta/conventions/ai_workflow.md` 未拆分、未重命名。
3. 本轮保持 `docs/_meta/conventions/ai_workflow.md` 现状。
4. 后续如需拆分为 `ai_collaboration_rules.md` + 操作化 `ai_workflow.md`，应单独批次或单独 CR 处理。
5. 不得把 C-02 记录为已完成。

边界说明：

1. CR-010 不定义技术事实。
2. CR-010 不替代 DEC。
3. CR-010 不修改 Architecture / Planning / Definition。
4. CR-010 不进入硬件、BOM、采购、源码、固件、部署、Docker 或服务。
5. G0 不是 P0-P10 正式阶段。
6. G0 只是治理基线收束工作包 / 历史说明。
