# Utility Scripts

## 测试脚本

| 脚本 | 说明 |
| --- | --- |
| `testing/orin_nx_mixed_stress_test.sh` | Orin NX CPU + GPU + 内存综合压力测试脚本，默认运行 20 分钟，并设置 `tj` 温度停止阈值。 |
| `testing/orin_nx_gpu_stress.cu` | 由综合测试脚本编译和调用的 CUDA GPU 压力程序。 |
