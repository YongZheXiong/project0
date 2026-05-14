# CR-011: 文档卫生与格式整理

## 状态

第一批已完成 / 残留暂缓

## 背景

Project0 已完成 G0 收束，CR-009 与 CR-010 已完成并收束。后续遗留问题按现有 CR / 阶段任务机制承接，不新增专门的后续治理跟踪文件。

上一轮只读 Plan 发现，当前仍存在一组不直接改变项目技术事实、但影响文档一致性、可读性和 Agent 理解的文档卫生问题，主要对应 C-11、C-19、C-20、C-21、C-22。

本 CR 用于为这些文档卫生问题建立受控修改边界，避免在清理格式和残留标记时误改 DEC、Architecture 技术事实、客观约束、主观需求或硬件 / BOM / 采购相关内容。

## 覆盖问题

本 CR 覆盖以下候选问题：

1. C-11：清理无效 AI citation / 孤立数字残留。
2. C-19：作者英文名统一为 `Yongzhe Xiong`。
3. C-20：`docs/00_definition/iter1_core_capabilities.md` 轻量格式修正。
4. C-21：`docs/00_definition/objective_constraints.md` 格式规范化。
5. C-22：`docs/00_definition/subjective_requirements.md` 结构整理。

本 CR 的目标包括：

1. 识别并受控清理无效 AI citation / 孤立数字残留。
2. 将作者英文名统一为 `Yongzhe Xiong`。
3. 修正 `iter1_core_capabilities.md` 中不必要的标题尾部反斜杠。
4. 将 `objective_constraints.md` 从原始记录式结构规范化为可读 Markdown 结构。
5. 将 `subjective_requirements.md` 中长段落一级标题整理为标题 + 正文结构。

## 修改范围

本 CR 只处理文档卫生、格式、结构和命名一致性。

建议纳入第一批 Execute 的文件白名单：

1. `README.md`
2. `docs/00_definition/iter1_core_capabilities.md`
3. `docs/00_definition/objective_constraints.md`
4. `docs/00_definition/subjective_requirements.md`

已知只读 Plan 发现：

1. `README.md` 中存在作者英文名 `Xiong Yongzhe`，建议统一为 `Yongzhe Xiong`。
2. `docs/00_definition/iter1_core_capabilities.md` 第六至第十节标题末尾存在反斜杠，建议轻量修正。
3. `docs/00_definition/objective_constraints.md` 使用原始记录式结构，建议 Markdown 格式规范化，但不得改变硬件、场地、预算、真机约束事实。
4. `docs/00_definition/subjective_requirements.md` 存在长段落被写成一级标题的问题，建议整理为标题 + 正文结构，但不得删减主观需求实质内容。
5. `docs/02_architecture/system_architecture.md`、`docs/02_architecture/interface_definition.md` 存在疑似无效 citation marker，但需人工单独确认是否纳入。

## 明确排除范围

本 CR 明确排除以下范围：

1. 不修改 DEC 决策内容。
2. 不修改 Architecture 技术事实。
3. 不处理硬件、BOM、采购、源码、固件、Docker 或服务文件。
4. 不修改构建、部署、安装、运行服务相关文件。
5. 不发布新版本。

默认排除文件包括：

1. 所有 `process/decisions/*` DEC 文件。
2. `docs/02_architecture/system_architecture.md`
3. `docs/02_architecture/interface_definition.md`
4. `docs/01_planning/file_structure_design_proposal.md`
5. `docs/DOC_INDEX.md`
6. `AGENTS.md`
7. `CHANGELOG.md`
8. 硬件、BOM、采购、源码、固件、Docker、服务、构建、部署相关文件。

如后续人工批准处理 Architecture 文件中的 citation marker，必须限定为 marker-only 清理，不得修改接口、模块、状态或技术事实。

## 执行原则

1. 本 CR 只处理文档卫生、格式、结构和命名一致性。
2. 本 CR 不改变项目技术事实。
3. 本 CR 不修改 DEC 决策内容。
4. 本 CR 不修改 Architecture 技术事实。
5. 本 CR 不削弱 `objective_constraints.md` 中的客观约束。
6. 本 CR 不删减 `subjective_requirements.md` 中的实质主观需求。
7. 本 CR 不处理硬件、BOM、采购、源码、固件、Docker 或服务文件。
8. 本 CR 不发布新版本。

具体执行时应遵循：

1. 删除无效 citation marker 前，必须确认其不是合法 Markdown 引用、列表编号、章节编号或历史说明。
2. 调整 `objective_constraints.md` 时，只允许改善 Markdown 结构、标题和段落可读性，不得改写场地、硬件、预算、真机验证、实验时间等客观事实。
3. 调整 `subjective_requirements.md` 时，只允许将长段落标题整理为更合理的标题 + 正文结构，不得删减、弱化或替换主观需求实质内容。
4. 调整 `iter1_core_capabilities.md` 时，只允许做轻量格式修正，不得改变迭代一核心能力定义。
5. 调整作者英文名时，只将明确作者名写法统一为 `Yongzhe Xiong`。

## 第一批建议修改文件

第一批建议 Execute 仅纳入以下文件：

1. `README.md`
2. `docs/00_definition/iter1_core_capabilities.md`
3. `docs/00_definition/objective_constraints.md`
4. `docs/00_definition/subjective_requirements.md`

第一批不建议修改 Architecture 文件、DEC 文件、CHANGELOG、DOC_INDEX、AGENTS 或任何硬件 / BOM / 采购 / 实现 / 部署相关文件。

## 暂缓或需单独确认事项

### Architecture citation marker

`docs/02_architecture/system_architecture.md` 和 `docs/02_architecture/interface_definition.md` 中存在疑似无效 citation marker，例如 `[14]` / `[4]`。

这些 Architecture 文件暂不纳入第一批正文修改。如后续确需处理，必须由人工单独确认，并限定为 marker-only 清理，不得修改接口、模块、状态或技术事实。

### file_structure_design_proposal.md 历史残留

`docs/01_planning/file_structure_design_proposal.md` 中存在大量历史 `[n]` 残留。

该文件暂不纳入本 CR 第一批执行，建议后续单独确认。若后续处理，应先判断这些标记是否属于历史规划说明、旧 citation 残留或其他合法编号，避免误删历史上下文。

## 风险与约束

主要风险：

1. 误删合法 Markdown 引用、列表编号、章节编号或历史说明。
2. 将 `objective_constraints.md` 的客观事实在格式规范化过程中误改、弱化或重写。
3. 将 `subjective_requirements.md` 的主观需求在结构整理过程中删减、合并过度或改变语气。
4. 将 Architecture 文件中的 marker 清理扩大为接口、模块、状态或技术事实修改。
5. 将文档卫生 CR 扩大为 DEC、Architecture、硬件、BOM、采购或实现层修改。

约束：

1. 不得误删合法 Markdown 引用、列表编号、章节编号、历史说明。
2. `objective_constraints.md` 只能格式规范化，不能削弱客观约束。
3. `subjective_requirements.md` 只能结构整理，不能删减实质主观需求。
4. 不得修改 DEC、Architecture 技术事实、硬件、BOM、采购、源码、固件、Docker 或服务文件。
5. 任何超出第一批建议修改文件白名单的修改，都必须重新经过人工确认。

## 验证方式

执行后至少进行以下只读验证：

1. `git status --short`
2. `git diff --name-only`
3. `git diff --stat`
4. `git diff --check`
5. 逐文件查看本 CR 批准范围内的 diff。
6. 检索作者名：
   - `Yongzhe`
   - `Xiong`
   - `Xiong Yongzhe`
   - `熊永哲`
7. 检索 citation / 残留候选：
   - `[1]`
   - `[2]`
   - `[3]`
   - `[4]`
   - `[5]`
   - `[14]`
   - `citation`
   - `来源`
   - `残留`
8. 核对是否未修改 DEC、Architecture 技术事实、硬件、BOM、采购、源码、固件、Docker 或服务文件。

## 当前结果

CR-011 草案已创建并提交：

1. `a6bfda26557a0565b93faf58a4ca77a1d7a5a2dd`
   `docs(cr): add CR-011 document hygiene cleanup draft`

CR-011 第一批正文修改已完成并提交：

1. `dcfb6f50a852810925fd3b3fc3bea2ee28832979`
   `docs(cr-011): clean definition document formatting`

第一批实际修改文件：

1. `README.md`
2. `docs/00_definition/iter1_core_capabilities.md`
3. `docs/00_definition/objective_constraints.md`
4. `docs/00_definition/subjective_requirements.md`

第一批完成项：

1. C-19 已完成：`README.md` 中作者英文名已统一为 `Yongzhe Xiong`。
2. C-20 已完成：`docs/00_definition/iter1_core_capabilities.md` 已删除第六至第十节标题尾部不必要反斜杠，仅做轻量格式修正。
3. C-21 已完成：`docs/00_definition/objective_constraints.md` 已整理为更清晰的 Markdown 结构；未削弱场地、硬件、预算、真机验证、实验时间等客观约束事实。
4. C-22 已完成：`docs/00_definition/subjective_requirements.md` 已从长段落一级标题整理为标题 + 正文结构；未删减主观需求实质内容。

C-11 当前状态：

1. 已完成无效 AI citation / 孤立数字残留的识别和暂缓边界确认。
2. 未执行 Architecture citation marker 清理。
3. 未处理 `docs/01_planning/file_structure_design_proposal.md` 历史 `[n]` 残留。
4. C-11 不写为完全完成，仓库中的全部 citation 残留不写为已经清零。

残留暂缓事项：

1. `docs/02_architecture/system_architecture.md` 与 `docs/02_architecture/interface_definition.md` 中疑似无效 citation marker 暂缓处理；后续如处理，必须人工单独确认，并限定为 marker-only 清理，不得修改接口、模块、状态或技术事实。
2. `docs/01_planning/file_structure_design_proposal.md` 中历史 `[n]` 残留暂缓处理；后续如处理，应先只读分类，避免误删历史上下文。
3. 本轮未修改 DEC、Architecture、CHANGELOG、DOC_INDEX、AGENTS、硬件、BOM、采购、源码、固件、Docker、服务、构建、部署相关文件。
