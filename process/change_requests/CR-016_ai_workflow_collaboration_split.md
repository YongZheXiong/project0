# CR-016: AI 协作规则与操作工作流拆分

## 状态

已完成

## 背景

C-02 只读审计确认：

1. `docs/_meta/conventions/ai_workflow.md` 当前存在。
2. `docs/_meta/conventions/ai_collaboration_rules.md` 当前不存在。
3. `ai_workflow.md` 内容同时包含长期 AI 协作规则和操作化工作流。
4. CR-010 已记录 C-02 未完成，建议后续单独批次或单独 CR 处理。

因此，本 CR 用于承接 C-02，建立 AI 协作规则与操作化工作流拆分的受控边界。

## 问题

当前 `ai_workflow.md` 同时承担两类职责：

1. 长期 AI 协作规则，例如 AI / Codex / Agent / 人工 / Git 分工、人工确认原则、Agent 红线和权限边界。
2. 操作化工作流，例如只读审计、修改计划、Plan -> Execute -> Verify -> Commit、diff 检查和提交前验证。

上述内容放在同一文件中，容易导致文件命名与内容定位不完全匹配，也可能让后续 Agent 不清楚哪些是长期协作规则，哪些是具体执行流程。

## 修改目标

本 CR 的目标是拆分 AI 协作规则与操作化工作流：

1. 新建 `docs/_meta/conventions/ai_collaboration_rules.md`，用于长期 AI 协作规则。
2. 收窄 `docs/_meta/conventions/ai_workflow.md`，用于操作化工作流。
3. 更新必要入口引用，使 `AGENTS.md`、`docs/DOC_INDEX.md`、`README.md` 和 `CHANGELOG.md` 与拆分后的职责边界一致。
4. 保持现有 AI 权限边界、人工确认机制、CR / DEC 约束和安全原则不变。

## 修改范围

后续 Execute 如经人工确认，可能影响以下文件：

1. `docs/_meta/conventions/ai_collaboration_rules.md`
2. `docs/_meta/conventions/ai_workflow.md`
3. `AGENTS.md`
4. `docs/DOC_INDEX.md`
5. `README.md`
6. `CHANGELOG.md`

`CHANGELOG.md` 只允许写入 `[Unreleased]`，不发版；C-18 后续统一处理发布节奏。

## 不修改范围

本 CR 不允许修改以下内容：

1. Architecture / Planning / Definition 文件。
2. 任何 `process/decisions/DEC-*.md` 文件。
3. 源码、接口、BOM、采购、部署文件。
4. 硬件、固件、配置、脚本、实验、报告、展示、数据文件。
5. 已确认技术结论、阶段路线、架构事实、接口事实或硬件事实。

本 CR 不改变 AI 权限边界。

本 CR 不削弱人工确认机制。

本 CR 不削弱 CR / DEC 约束。

本 CR 不削弱安全、急停、人工接管、电源边界等安全原则。

## 拆分原则

拆分时应遵循以下原则：

1. 只做职责拆分和引用同步，不新增项目技术事实。
2. 只迁移或整理已有治理规则，不扩大 Agent 权限。
3. 不把拆分过程做成全量重写治理体系。
4. 不把 G0 写成当前长期主线。
5. 不把 P2-P6 代码实现或 P7-P10 迭代二增强提前写成当前任务。
6. 如发现现有内容需要实质性改写，应先回到 Plan 并列出影响范围。

## 文件职责边界

拆分后的建议职责如下：

1. `docs/_meta/conventions/ai_collaboration_rules.md`
   - 记录长期 AI 协作规则。
   - 说明 AI / Codex / Agent / 人工 / Git 分工。
   - 说明人工确认原则、Agent 红线、权限边界、禁止事项。
   - 承接 CR / DEC 约束和安全底线。

2. `docs/_meta/conventions/ai_workflow.md`
   - 记录操作化工作流。
   - 说明只读审计、修改计划、执行、验证和提交前检查。
   - 说明 Plan -> Execute -> Verify -> Commit。
   - 说明 diff 检查、提交前验证和 Agent 提示词使用流程。

3. `AGENTS.md`
   - 继续作为 Agent 进入仓库前的入口规则文件。
   - 只引用或概括两个 conventions 文件，不重复完整细则。

4. `docs/DOC_INDEX.md`
   - 更新索引和依赖导航，反映新增协作规则文件。

5. `README.md`
   - 更新入口导航摘要，不定义新的治理细则。

6. `CHANGELOG.md`
   - 仅在 `[Unreleased]` 记录治理文件拆分，不发布版本。

## 风险与约束

主要风险：

1. 拆分后入口引用不一致，导致 Agent 只读取部分规则。
2. `AGENTS.md` 与 conventions 文件重复过多，造成职责重叠。
3. `ai_workflow.md` 收窄时误删必要操作流程。
4. `ai_collaboration_rules.md` 新建时写成阶段任务清单，而不是长期规则。
5. 拆分过程中误改技术事实、阶段事实或安全边界。
6. `CHANGELOG.md` 误发版或提前处理 C-18 发布节奏。

约束：

1. 本 CR 必须先完成 Plan，再经人工确认后才能 Execute。
2. Execute 只能修改人工批准的文件。
3. 不允许在本 CR 中修改 Architecture / Planning / Definition、DEC、源码、接口、BOM、采购或部署文件。
4. 不允许削弱安全、急停、人工接管、电源边界等安全底线。
5. 不允许改变 CR / DEC 约束或绕过人工确认。

## 执行结果

本轮已完成 AI 协作规则与操作工作流拆分。

实际修改文件为：

1. `process/change_requests/CR-016_ai_workflow_collaboration_split.md`
2. `docs/_meta/conventions/ai_collaboration_rules.md`
3. `docs/_meta/conventions/ai_workflow.md`
4. `AGENTS.md`
5. `docs/DOC_INDEX.md`
6. `README.md`
7. `CHANGELOG.md`

执行内容如下：

1. 新建 `docs/_meta/conventions/ai_collaboration_rules.md`，用于长期 AI 协作规则、角色分工、权限边界、Agent 红线、CR / DEC 约束和安全底线。
2. 收窄 `docs/_meta/conventions/ai_workflow.md`，用于只读审计、修改计划、Plan -> Execute -> Verify -> Commit、diff 检查、提交前验证和 Agent 提示词使用流程。
3. 同步 `AGENTS.md`、`docs/DOC_INDEX.md`、`README.md` 中的入口引用。
4. 在 `CHANGELOG.md` 的 `[Unreleased]` 中记录本次治理文件拆分，未发版。

本轮未修改以下范围：

1. Architecture / Planning / Definition 文件。
2. 任何 `process/decisions/DEC-*.md` 文件。
3. 源码、接口、BOM、采购、部署文件。
4. 硬件、固件、配置、脚本、实验、报告、展示、数据文件。

本轮没有改变或削弱以下内容：

1. AI 权限边界。
2. 人工确认机制。
3. CR / DEC 约束。
4. 安全、急停、人工接管、电源边界等安全原则。
5. 项目技术事实、阶段路线、架构事实、接口事实或硬件事实。

## 验证方式

后续如进入 Execute，至少执行以下验证：

1. `git status --short`
2. `git diff --name-only`
3. `git diff --check`
4. 检查实际修改文件是否只包含人工批准文件。
5. 检查 `ai_collaboration_rules.md` 是否只承载长期 AI 协作规则。
6. 检查 `ai_workflow.md` 是否收窄为操作化工作流。
7. 检查 `AGENTS.md`、`docs/DOC_INDEX.md`、`README.md` 引用是否一致。
8. 检查 `CHANGELOG.md` 是否只写入 `[Unreleased]`，且未发版。
9. 检查是否未修改 Architecture / Planning / Definition、DEC、源码、接口、BOM、采购或部署文件。
10. 检查是否未改变 AI 权限边界、人工确认机制、CR / DEC 约束和安全原则。
