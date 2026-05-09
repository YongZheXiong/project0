# 项目0（Project Zero）

## 项目概述

项目0是一个单人solo开发的具身智能小车平台项目，面向广东工业大学教学楼单层回字形走廊真实场景，目标是构建一个具备感知—决策—执行闭环、语义导航能力、安全约束机制的类产品级基础平台，并在此基础上进行能力增强与科研验证。

## 当前状态

| 项目 | 状态 |
|------|------|
| 当前阶段 | P1.3：硬件方案与采购 |
| 当前治理状态 | G0 核心治理收束已完成，治理规则与入口文件已对齐 |
| 当前主线目标 | 回到 P1.3，完成 BOM 与采购清单 |
| 当前版本 | V0.2.5-dev / governance 中 |

## 硬件平台（已确认摘要）

- 计算：Jetson Orin NX 16GB
- 激光雷达：Livox Mid360
- 深度相机：Intel RealSense D435
- 底盘：四轮差速（JGB-520 x 4）

其余硬件缺口、采购优先级与 BOM 以 P1.3 阶段输出的采购清单为准，README 不单独定义新的硬件结论。

## 文档导航

- [docs/DOC_INDEX.md](docs/DOC_INDEX.md)：文档索引与依赖关系
- [AGENTS.md](AGENTS.md)：AI / Codex 协作规则
- [docs/_meta/conventions/ai_workflow.md](docs/_meta/conventions/ai_workflow.md)：AI 工作流规范
- [docs/_meta/conventions/document_governance.md](docs/_meta/conventions/document_governance.md)：文档治理规范
- [process/change_requests/](process/change_requests/)：跨文件变更请求机制
- [process/decisions/](process/decisions/)：关键决策记录
- [CHANGELOG.md](CHANGELOG.md)：版本记录

README 只是仓库入口摘要，不替代 DOC_INDEX、DEC 决策记录、架构文档和 CHANGELOG。

## 当前真实目录结构

```text
project0/
├── config/
├── data/
├── docs/
│   ├── 00_definition/
│   ├── 01_planning/
│   ├── 02_architecture/
│   ├── 04_deployment/
│   ├── _meta/
│   └── DOC_INDEX.md
├── experiments/
├── firmware/
├── hardware/
│   └── README.md
├── presentation/
├── process/
│   ├── change_requests/
│   ├── decisions/
│   ├── learning_notes/
│   └── weekly_log/
├── reports/
├── scripts/
├── simulation/
├── src/
├── AGENTS.md
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## 规划中目录

以下目录属于后续规划，当前尚未创建，不属于上方当前真实目录树：

- `docs/03_design/`
- `docs/05_calibration/`
- `docs/06_testing/`
- `docs/07_iter2/`

## 版本记录

见 [CHANGELOG.md](CHANGELOG.md)。

## 作者

Xiong Yongzhe
