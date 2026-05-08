# G0 已有文件只读审计报告

## 1. 审计范围与方法
本次审计按 CR-004 要求，仅做只读检查，不修改任何已有文件。  
读取并核对了以下规则与事实源：`AGENTS.md`、`docs/DOC_INDEX.md`、`docs/_meta/conventions/ai_workflow.md`、`docs/_meta/conventions/document_governance.md`、`process/change_requests/CR-004_existing_files_audit_and_classification.md`，以及当前仓库中已存在的 `README.md`、`CHANGELOG.md`、`process/change_requests/`、`process/decisions/`、`docs/00_definition/`、`docs/01_planning/`、`docs/02_architecture/`、`docs/04_deployment/`、`hardware/`、`src/`、`firmware/`、`config/`、`scripts/`、`reports/`、`presentation/`、`experiments/`、`simulation/`、`data/`。

审计方法是按层级核对事实源、状态标签、颗粒度、命名一致性与下游误读风险，并重点检查 P1.3 采购前置风险。

## 2. 总体结论
当前仓库可以继续 G0 收束，而且不需要大规模重写。  
安全边界、人工接管链路、电源边界、系统管理边界在 DEC 与架构层之间总体一致，没有发现需要推翻路线的冲突。  
但仍存在一个明确的 P1.3 前置问题：硬件命名基线尚未完全统一，尤其是电机型号与少量传感器命名写法混用，会直接影响 BOM、采购、接线图和硬件标注。

结论上，G0 应继续，但 P1.3 不应在当前命名状态下直接进入采购。后续应采用小步、分 CR 的方式修复，而不是整仓重写。

## 3. 按文档层级的状态判断

### 3.1 项目治理层
`README.md`、`AGENTS.md`、`CHANGELOG.md`、`docs/DOC_INDEX.md`、`docs/_meta/`、`process/change_requests/` 的治理职责基本清楚，且 `DOC_INDEX` 已能把大部分文档状态分层标出。  
主要问题是 `README.md` 仍放入了硬件摘要，而该摘要目前没有和架构层命名完全统一；`CHANGELOG.md` 的最新版本段落也还没完全收口。  
这一层不阻塞 P1.3 的安全边界，但会影响采购判断和版本追踪的清晰度，建议继续保持“入口摘要 + 索引导航”的定位。

### 3.2 项目定义层
`docs/00_definition/` 的状态相对稳定，且与当前场景、硬件基础和迭代边界一致。  
其中 `objective_constraints.md` 明确了 `D435` 而不是 `D435i`，`system_positioning.md` 也保持了“真机闭环、非纯仿真”的主线。  
这一层目前没有发现会直接阻塞 P1.3 的问题，适合作为上游事实源继续承接。

### 3.3 P1 规划层
`docs/01_planning/iter1_function_list.md`、`iter1_function_items.md` 与 DEC-003/004/005/006/007/008/014/018/019 的路线总体一致，没有发现把废弃 DEC 重新写回当前事实源的情况。  
主要问题有两个：`file_structure_design_proposal.md` 仍像“当前真实目录说明”，以及 `iter1_function_items.md` 存在重复、交叠的结构块，颗粒度不够干净。  
这一层不直接阻塞 P1.3，但会影响 Agent 对“哪些是当前事实、哪些只是规划”的判断。

### 3.4 系统架构层
`docs/02_architecture/system_architecture.md`、`compute_comm_architecture.md`、`power_architecture.md`、`hardware_architecture.md`、`software_architecture.md`、`interface_definition.md` 整体上已经形成一致的架构骨架。  
好的一面是：人工接管、急停、供电边界、系统管理权、语义导航归属都已经和 DEC 对齐。  
需要注意的是：`system_architecture.md` 里仍出现一次 `D435i`，`interface_definition.md` 还保留骨架版接口命名/归属待统一的写法，属于状态清晰度问题，不是路线冲突。  
这一层的主风险仍然是命名统一，而不是架构推翻。

### 3.5 决策事实源层
`DEC-003`、`DEC-004`、`DEC-005`、`DEC-006`、`DEC-007`、`DEC-008`、`DEC-014`、`DEC-018`、`DEC-019` 的状态清楚，且彼此之间没有发现直接冲突。  
`DEC-013` 已正确标为废弃，不应再作为事实源。  
`DEC-009` 为空文件，应继续视为异常待复核，不能当作有效决策事实使用。

### 3.6 部署 / 实现 / 测试 / 报告层
`docs/04_deployment/`、`src/`、`firmware/`、`hardware/`、`config/`、`scripts/`、`reports/`、`presentation/`、`experiments/`、`simulation/`、`data/` 目前都还是占位或低完成度状态，且没有伪装成正式完备文档。  
这一层的状态是可接受的，但需要继续保持“占位就是占位”的标识，避免后续 Agent 误读为已完成实现层。

## 4. A 类问题：P1.3 前必须修复
- 编号：A-01
- 问题：硬件命名基线未统一。仓库中同时出现 `JGB-520 x4`、`GB37-520`、`Mid360` / `Mid-360`、以及面向未来增强语境中的 `D435i`。其中电机型号冲突会直接影响 BOM、采购、接线图和硬件标注，传感器写法混用会影响标定、照片索引和后续接口命名。
- 涉及文件：`README.md`、`docs/00_definition/objective_constraints.md`、`docs/02_architecture/system_architecture.md`、`docs/02_architecture/compute_comm_architecture.md`、`docs/02_architecture/power_architecture.md`、`docs/02_architecture/hardware_architecture.md`、`docs/02_architecture/diagrams/vehicle_hardware_topology.drawio`
- 为什么是 A 类：这是直接影响 P1.3 BOM、采购、接线和硬件命名的前置事实，不先收束就会把后续采购和装配带偏。
- 建议后续 CR：`CR-005`，统一 P1.3 硬件命名基线，并同步入口摘要、规划层和架构层的用名。
- 是否允许 Agent 修复：允许，但必须放进新的 CR 后再执行。
- 是否需要人工确认：需要，尤其是电机型号与传感器写法的 canonical name。

## 5. B 类问题：G0 阶段建议修复
- 编号：B-01
- 问题：`docs/01_planning/file_structure_design_proposal.md` 仍以“Git仓库实际使用”的语气写目录树，且混合了当前存在目录、规划目录和未来目录，容易被误读为现状说明。
- 涉及文件：`docs/01_planning/file_structure_design_proposal.md`、`docs/DOC_INDEX.md`、`README.md`
- 为什么是 B 类：它主要影响文档状态清晰度和 Agent 认知，不直接阻塞 P1.3，但会制造目录误读。
- 建议后续 CR：`CR-006`，把该文件明确定性为“规划方案 / 历史结构方案 / 非当前真实目录”。
- 是否允许 Agent 修复：允许，但仅在后续 CR 中做定性修正。
- 是否需要人工确认：需要。

- 编号：B-02
- 问题：`docs/01_planning/iter1_function_items.md` 存在重复和交叠的内容块，尤其是任务调度相关段落，颗粒度不够干净。
- 涉及文件：`docs/01_planning/iter1_function_items.md`
- 为什么是 B 类：它影响文档维护和 Agent 理解，但与现有 DEC 的主路线没有直接冲突。
- 建议后续 CR：`CR-007`，收敛重复段落，整理层级和职责边界。
- 是否允许 Agent 修复：允许，但应在后续 CR 中逐段收口。
- 是否需要人工确认：需要。

- 编号：B-03
- 问题：`process/decisions/DEC-009-semantic_location_owned_by_ap_manager.md` 为空文件，却仍留在决策层目录中，状态应继续视为异常待复核。
- 涉及文件：`process/decisions/DEC-009-semantic_location_owned_by_ap_manager.md`、`docs/DOC_INDEX.md`
- 为什么是 B 类：它主要是决策层状态清晰度问题，不直接阻塞 P1.3，但会影响后续语义/位置相关判断。
- 建议后续 CR：`CR-007` 或独立的 DEC 复核 CR，先人工确认它是补全、废弃还是保留异常状态。
- 是否允许 Agent 修复：不建议直接修复，需人工确认后再进入后续 CR。
- 是否需要人工确认：需要。

- 编号：B-04
- 问题：`docs/02_architecture/interface_definition.md` 仍是骨架版 V0.1，部分接口名称和归属尚未冻结，例如 `QuerySemanticPose/GetSemanticPose`、`TriggerEmergencyStop`、`NavigateToSemantic.action` 的最终归属。
- 涉及文件：`docs/02_architecture/interface_definition.md`、`docs/02_architecture/software_architecture.md`
- 为什么是 B 类：这是接口状态和颗粒度问题，不是当前安全或采购路线冲突，但若不收口会影响实现落地。
- 建议后续 CR：`CR-007`，冻结一版最终命名与归属，再进入实现。
- 是否允许 Agent 修复：允许，但要在后续 CR 中完成。
- 是否需要人工确认：需要。

- 编号：B-05
- 问题：`CHANGELOG.md` 的最新条目 `0.2.5` 记录未收口，日期段仍是半截状态，版本史不够完整。
- 涉及文件：`CHANGELOG.md`、`README.md`
- 为什么是 B 类：它影响版本追踪和治理清晰度，但不直接影响 P1.3 采购。
- 建议后续 CR：可并入 `CR-007`，顺手把版本记录收口。
- 是否允许 Agent 修复：允许，但应按版本记录规范处理。
- 是否需要人工确认：需要。

## 6. C 类问题：暂缓处理
- 编号：C-01
- 问题：`docs/01_planning/file_structure_design_proposal.md` 中列出的 `docs/03_design/`、`docs/05_calibration/`、`docs/06_testing/`、`docs/07_iter2/` 属于后续阶段目录，不应在 G0 直接创建。
- 暂缓原因：这部分属于未来阶段规划，不是当前 P1.3 或 G0 必须落地的内容。
- 后续触发时机：进入对应阶段，或另一个明确的 CR 允许创建目录骨架时再处理。

- 编号：C-02
- 问题：`docs/01_planning/iter1_function_list.md`、`docs/02_architecture/system_architecture.md`、`docs/02_architecture/software_architecture.md` 中的迭代二增强说明（多传感器融合、回环、LLM、语义地图等）仍属于未来增强路径。
- 暂缓原因：这些内容已经被标明为迭代二方向，当前只需保留边界，不应在 G0 展开修复或补写。
- 后续触发时机：P7-P10 或明确进入迭代二相关 CR 时再处理。

## 7. file_structure_design_proposal.md 专项判断
当前它不适合作为真实目录说明。  
它应被定性为“规划方案”或更准确地说“历史结构方案 / 非当前真实目录”。  
误导点主要有两个：一是标题和正文把它写得像 Git 仓库实际使用目录树，二是它同时混入了未来目录、规划文件和当前目录，缺少清楚的状态边界。

后续建议单独开 CR 修正，目标不是扩展目录，而是把它从“当前真实目录说明”降级成“仅供规划参考的结构方案”，并让 `docs/DOC_INDEX.md` 继续保持当前真实文档地图的权威地位。

## 8. P1.3 前置事实专项判断
- `D435 / D435i`：当前定义层和大部分架构层都指向 `D435`，`system_architecture.md` 里出现的 `D435i` 应视为命名漂移，不能当作另一台已确认硬件。
- `Livox Mid360 / Mid-360`：仓库里存在两种写法，属于同一设备的命名不统一。建议在 P1.3 采购和照片索引前统一一个 canonical name。
- `JGB-520 / GB37-520`：这是当前最直接的命名冲突，必须先定稿再进 BOM 和采购。
- `飞智黑武士2 + 2.4G USB 接收器`：与 DEC-018、计算通信架构、硬件架构、电源架构一致，没有发现冲突。
- `人工接管链路`：已稳定对齐为“手柄 → 2.4G USB 接收器 → Orin NX → teleop / 手动控制节点 → cmd_vel → 底盘桥接 → UART → STM32”，当前不需改路线。
- `急停边界`：已稳定对齐为“纯硬件切断动力支路，不切计算与感知支路”，与 DEC-014、DEC-019、DEC-008 一致。
- `电源边界`：已稳定对齐为主电池统一供能、动力/计算/传感器控制分支三段式，不需要重写。
- `是否需要硬件命名基线文件`：需要。现阶段至少需要一个最小的硬件命名基线，避免 README、架构层和未来 BOM 各写各的名字。
- `是否需要单独 DEC_INDEX`：当前不急需，`docs/DOC_INDEX.md` 已承担大部分索引职责。
- `是否需要文件状态索引`：可作为后续治理增强项考虑，但当前不是 P1.3 前置阻塞项。

## 9. 建议拆分的后续 CR
- CR 编号建议：CR-005
- 名称：P1.3 硬件命名基线统一
- 目标：统一 `JGB-520 / GB37-520`、`Mid360 / Mid-360`、`D435 / D435i` 的 canonical name，并同步入口摘要、规划层、架构层和图纸文本。
- 允许修改范围：`README.md`、`docs/01_planning/iter1_function_list.md`、`docs/01_planning/iter1_function_items.md`、`docs/02_architecture/system_architecture.md`、`docs/02_architecture/compute_comm_architecture.md`、`docs/02_architecture/power_architecture.md`、`docs/02_architecture/hardware_architecture.md`、`docs/02_architecture/interface_definition.md`、`docs/02_architecture/diagrams/vehicle_hardware_topology.drawio`
- 禁止修改范围：所有 DEC 文件、定义层主事实、未来目录创建、实现层代码
- 优先级：最高，P1.3 前必须先做

- CR 编号建议：CR-006
- 名称：`file_structure_design_proposal.md` 定性修正
- 目标：把该文件从“当前真实目录说明”修正为“规划方案 / 历史结构方案 / 非当前真实目录”
- 允许修改范围：`docs/01_planning/file_structure_design_proposal.md`、`docs/DOC_INDEX.md`、`README.md`
- 禁止修改范围：定义层、DEC 结论、实现层、未来目录树的直接创建
- 优先级：高，属于 G0 收束

- CR 编号建议：CR-007
- 名称：P1 规划与接口骨架收口
- 目标：收敛 `iter1_function_items.md` 的重复段落，冻结 `interface_definition.md` 的接口命名与归属，并按需复核 `DEC-009` 的异常状态
- 允许修改范围：`docs/01_planning/iter1_function_items.md`、`docs/02_architecture/interface_definition.md`、`docs/DOC_INDEX.md`，必要时经人工确认后再处理 `process/decisions/DEC-009-semantic_location_owned_by_ap_manager.md`
- 禁止修改范围：`DEC-013`、`DEC-014`、`DEC-018`、`DEC-019` 等已确认结论本身，未来目录直接扩展，代码层
- 优先级：中等，放在硬件命名基线之后

## 10. 明确不建议现在做的事
现在不建议做的事包括：
1. 不要补写 P2-P6 或 P7-P10 的完整实现内容。
2. 不要把 `file_structure_design_proposal.md` 当成当前真实目录去照搬创建未来目录。
3. 不要在硬件命名未统一前直接进入 BOM、采购清单或接线图定稿。
4. 不要重写整个 `docs/` 或整个 `process/decisions/`。
5. 不要把 `interface_definition.md` 的骨架版直接当最终冻结版使用。

## 11. 最终结论
G0 应继续，而且可以继续收束。  
下一步最小动作是先开 `CR-005` 统一硬件命名基线，再开 `CR-006` 把 `file_structure_design_proposal.md` 降级为规划方案，随后再视需要做 `CR-007` 的规划与接口骨架收口。  
当前还不能马上进入 P1.3 采购，因为硬件命名没有完全统一。  
必须先完成的最小修复只有两类：硬件命名基线统一，以及把规划方案和骨架文档的状态边界标清。
