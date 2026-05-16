# ADR-0001: LLM Provider Selection — DeepSeek as Primary with Provider Abstraction

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Dylan

## Context

劳动合同审查 agent 需要 LLM 满足：
- 强中文理解，能准确处理法律术语、条款引用、案例语言
- Portfolio 级项目预算约束（目标单次审查成本 < ¥0.5）
- 不同检测策略对模型能力要求差异大：从字段抽取（轻量）到跨条款推理（重型）

Taxonomy 的 5 层 detection strategy 决定了 "一个模型打天下" 会在简单类目上过付钱、在复杂类目上欠性能。

## Decision Drivers

按优先级：

1. **中文法律文本质量** — deal-breaker
2. **成本** — 10 类目 × eval set × 多轮迭代，total tokens 很大
3. **推理能力** — `non_compete`、`wage_composition` 等需要跨条款推理
4. **Provider 灵活度** — 不能 lock-in 单一 vendor

## Considered Options

1. **DeepSeek（V3 + R1）** — 中文性价比顶级，R1 推理强
2. **Claude Sonnet** — 推理强、可解释好，但中文略弱、价格 ~10x
3. **GPT-4o** — 通用强、中文一般、价格高
4. **通义千问 Qwen-Max** — 中文优秀、阿里生态、推理类略新
5. **智谱 GLM-4** — 中文好、价格中等

## Decision

**Chosen: DeepSeek 为主力，按 detection strategy 分层路由，代码层走 `LLMClient` 抽象**

路由配置：
- `rule_assisted_llm` / `rag_light_llm` → DeepSeek-V3
- `rag_heavy_llm` → DeepSeek-V3
- `multi_step_reasoning` → DeepSeek-R1

实现层：所有 LLM 调用经过 `LLMClient` 接口，provider 由配置项决定，业务代码与具体 SDK 解耦。

### Why this option

- DeepSeek 在中文法律任务上接近第一梯队，价格约为 Claude 的 1/10
- V3 + R1 双模型自然覆盖任务复杂度全谱
- 抽象层成本 < 100 行代码，但 P4 跨模型 benchmark 时收益巨大
- 避免 vendor lock-in：业务代码零改动即可切换 provider
- 服务器在国内（腾讯云），DeepSeek API 国内直连，延迟低

### Why not the others

| Option | Reason rejected |
|--------|-----------------|
| Claude Sonnet | 中文法律性价比明显劣于 DeepSeek；国内访问需代理；保留为 P4 benchmark 对照组 |
| GPT-4o | 中文表现不如 DeepSeek，价格高，国内访问受限 |
| Qwen-Max | 备选，但推理类口碑历史上略弱于 DeepSeek-R1；保留为备用 |
| GLM-4 | 备选，性价比相近但生态稍弱；保留为备用 |

## Consequences

### Positive
- token 成本压低一个数量级，eval 可放心多轮迭代
- 双模型自然分层，避免简单任务过付费
- 抽象层让 P4 跨模型 benchmark 几乎零开发成本
- 中文 SFT 数据更贴合法律语料
- 国内访问延迟低、合规风险低

### Negative / Accepted Tradeoffs
- DeepSeek API 历史稳定性略弱于 Claude/GPT（偶发限流、维护窗口）
- 国内 LLM provider 政策不确定性高于海外
- DeepSeek 的 tool use / 结构化输出能力略弱于 Claude

### Mitigations
- `LLMClient` 抽象 + retry / fallback 机制（主用 V3，超时 fallback 到 Qwen）
- 结构化输出走 JSON schema + 解析失败重试
- 备用 provider（Qwen / GLM）保持配置可切换，季度回归测试

## Confirmation

- **P2 通过条件**：`probation_period` 类目 P≥0.9 R≥0.85 即视为模型选型可行
- **P4 benchmark**：DeepSeek vs Claude vs Qwen 在完整 eval set 上 head-to-head
- **回头改的触发条件**：若某类目 DeepSeek 落后 Claude > 10%，将该类目路由切到 Claude（业务代码零改动）

## References

- 内部：Taxonomy spec (`docs/taxonomy.yaml` — 待写)
- 内部：Detection strategy spec (`docs/strategies.md` — 待写)
- 待补：DeepSeek 中文法律 benchmark 公开数据
