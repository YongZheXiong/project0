# Utility Scripts

> 状态：通用 Orin 压力脚本可继续使用；所有 `stm32_*` 脚本均为上一平台历史工具，不支持 H60 协议、显式 ARM、状态机或故障字段，不得用于 H60 上电或运动准入。

## 测试脚本

| 脚本 | 说明 |
| --- | --- |
| `check_release_state.py` | 只读检查 README 当前阶段、开发版本、CHANGELOG 入口、阶段门、开发预发布与正式 Git 标签；在 P2 完成前阻止正式 `v1.1`，不自动提交、打标签或推送。 |
| `testing/orin_nx_mixed_stress_test.sh` | Orin NX CPU + GPU + 内存综合压力测试脚本，默认运行 20 分钟，带 `tj` 温度上限保护。 |
| `testing/orin_nx_gpu_stress.cu` | CUDA GPU 压力测试程序源码，由综合测试脚本编译和调用。 |

## 版本提醒

在每次恢复项目、阶段门变化和准备结束较大变更时运行：

```bash
python3 scripts/check_release_state.py
```

该脚本只做本地检查与提醒。正式发布仍需先完成阶段验收，再由用户批准提交、标签和推送；不采用“每天自动发布”。

阶段内已验证的任务可以形成普通开发提交；对外有价值的检查点可以发布递增的 `v1.1-dev.N` 开发预发布，并继续保留新的 `v1.1-dev / Unreleased` 入口。H0-H8 全部 `PASS` 时，脚本只把状态提升为“进入正式发布审查”；真实代码、通信/里程计/接管证据、阶段记录、CHANGELOG、发布 diff 和用户授权仍需人工复核。
