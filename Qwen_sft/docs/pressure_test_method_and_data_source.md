# 压测方法与数据来源说明

## 1. 本轮压测是如何进行的

本轮压测采用本地 OpenAI 兼容接口 + 多并发请求回放的方式，目标是评估系统性能维度：

- 响应延迟（mean, P50, P95, P99, max）
- 吞吐（QPS）
- 调用稳定性（错误率、非 200 响应样本）

执行链路如下：

1. 启动 LoRA 推理服务
- 服务脚本读取 Base 模型 + LoRA Adapter，暴露接口：
  - GET /health
  - GET /v1/models
  - POST /v1/chat/completions
- 服务文件： [serve_lora_openai.py](serve_lora_openai.py)

2. 并发压测脚本驱动请求
- 从数据集中读取 system + user 作为输入请求
- 按并发级别启动线程池，循环发送请求
- 统计：成功数、失败数、错误率、QPS、延迟分位
- 脚本文件： [run_load_benchmark.py](run_load_benchmark.py)

3. 统一编排脚本串联 3B 和 7B
- 先跑 3B 主压测（并发 1/2/4/8）
- 再跑 7B 小流量压测（并发 1/2/4）
- 最后合并出对照摘要
- 编排文件： [run_online_stress_compare.sh](run_online_stress_compare.sh)

4. 输出报告
- 3B 报告： [output/online_bench/reports/bench_3b.json](output/online_bench/reports/bench_3b.json)
- 7B 报告： [output/online_bench/reports/bench_7b_small.json](output/online_bench/reports/bench_7b_small.json)
- 汇总报告： [output/online_bench/reports/bench_compare_summary.md](output/online_bench/reports/bench_compare_summary.md)

## 2. 本轮压测参数

- 测试数据集： datasets/json/dataset_internal_20_run9_1.json
- Prompt 采样数：20
- max_tokens：64
- 3B：每个并发级别 40 请求
- 7B：每个并发级别 24 请求
- 运行模式：单卡串行生成（max-concurrent-generations=1）

## 3. 本轮核心压测结果（系统性能）

| 模型 | 并发 | QPS | P95(s) | P99(s) | 错误率 |
|---|---:|---:|---:|---:|---:|
| 3B | 1 | 0.177 | 7.506 | 7.535 | 0.00% |
| 3B | 2 | 0.179 | 14.389 | 14.637 | 0.00% |
| 3B | 4 | 0.177 | 27.189 | 28.053 | 0.00% |
| 3B | 8 | 0.181 | 50.871 | 52.031 | 0.00% |
| 7B | 1 | 0.225 | 5.814 | 6.333 | 0.00% |
| 7B | 2 | 0.212 | 11.577 | 11.864 | 0.00% |
| 7B | 4 | 0.230 | 19.789 | 20.185 | 0.00% |

结论：
- 当前测试条件下，7B 在 1/2/4 并发均表现出更高吞吐和更低尾时延。
- 本轮稳定性表现良好，错误率均为 0%。

## 4. 现在压测数据是怎么来的

当前压测请求来自内部测试集文件：
- [datasets/json/dataset_internal_20_run9_1.json](datasets/json/dataset_internal_20_run9_1.json)

生成方式：
- 读取每条样本中的 messages
- 仅抽取 system + user 组成请求输入
- 不使用原始 assistant 作为输入
- 按 prompt-limit 截取前 20 条构建压测请求池

这意味着：
- 本轮压测更偏向“系统压测快速验证”
- 数据分布只覆盖内部测试集，外部分布尚未纳入
- 样本量偏小，不适合作为最终 SLA 基线

## 5. 是否需要用内部+外部测试集重跑压测

建议：需要重跑，并且建议作为上线前必做项。

原因：
- 系统性能不仅受模型影响，也受输入长度、术语复杂度、问法风格影响。
- 外部测试集通常更接近分布漂移场景，能更真实地暴露尾时延和稳定性风险。
- 当前仅 20 条内部样本，统计置信度不足，容易高估稳定性。

建议重跑方案：

1. 数据侧
- 使用内部 + 外部两套数据分别压测并汇总
- 建议每套至少 100 至 300 条请求（可分桶：短/中/长输入）

2. 场景侧
- 3B 主场景：并发 1/2/4/8/12
- 7B 对照场景：并发 1/2/4/6
- 每并发建议请求数 >= 100

3. 监控侧
- 保留已有 QPS/P95/P99/错误率
- 增加：超时率、HTTP 5xx 比例、首 token 时延（如可采集）
- 增加按数据域拆分报表：internal vs external

4. 判定侧
- 先定义上线阈值（示例）：
  - 错误率 <= 0.5%
  - P95 <= 目标阈值
  - P99 <= 目标阈值
- 通过后再进入灰度

## 6. 当前文档对应的关键脚本与报告

- 服务脚本： [serve_lora_openai.py](serve_lora_openai.py)
- 压测脚本： [run_load_benchmark.py](run_load_benchmark.py)
- 编排脚本： [run_online_stress_compare.sh](run_online_stress_compare.sh)
- 汇总报告： [output/online_bench/reports/bench_compare_summary.md](output/online_bench/reports/bench_compare_summary.md)
