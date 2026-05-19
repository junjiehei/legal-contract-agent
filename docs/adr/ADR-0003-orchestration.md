# ADR-0003: Orchestration — Custom vs Framework

**Status**: Draft
**Date**: TODO
**Deciders**: Dylan
**Related**: ADR-0001 (LLM Selection), ADR-0002 (Vector DB)

## Context

合同审查 pipeline 的核心数据流：

```
合同输入 → ingest/parser → segmenter
  → router（按 taxonomy 类目分发）
  → detector（per-category 检测）
    └→ extractor（LLM 抽字段）
    └→ rule_engine（规则验证）
    └→ rag_retriever（法条/判例检索）
  → verifier（防幻觉 + 引用验证）
  → aggregator（结果合并 + 报告生成）
```

需要决定：**用现成 orchestration 框架（LangChain / LlamaIndex / LangGraph）还是自研**？

时代背景（2026 年）：
- LangChain 经历过多次重大重构，社区共识"抽象比它解决的问题还多"
- LangGraph（LangChain 团队新作）是 graph-based agent，更轻更现代
- LlamaIndex 仍是 RAG 主流，更聚焦
- 一些团队选择"自研最小化 + 选择性使用专项库"

## Decision Drivers

按优先级：

1. **代码可解释性**（最高）：每行代码我能讲清楚为什么这么写。review 时必须能 walk through 完整路径。
2. **不被框架锁死**：LangChain 历史上 breaking change 频繁；选了框架≠不能维护
3. **学习曲线**：solo dev，时间宝贵；框架学习成本 vs 自研代码成本要算清
4. **未来扩展性**：P5a 要做 chat agent，orchestration 选型不能阻塞 chat agent 用 Claude Agent SDK
5. **debugging 体验**：能加 print/breakpoint，看清楚 LLM 调用前后的中间状态

## Considered Options

1. **LangChain 全家桶** — 最流行，最多教程，但抽象重；2026 年使用 = "落后两年"信号。
2. **LangGraph**（LangChain 团队新作）— graph-based agent 框架，更现代、更轻，状态管理清晰。
3. **LlamaIndex 全家桶** — RAG 聚焦，更轻于 LangChain，但 chat agent 能力弱。
4. **完全自研（< 500 行核心）** — 直接调 LLM SDK + 自己写 router/verifier/orchestrator。最大化可解释性。
5. **混合：自研核心 + LlamaIndex 仅 retrieval** — 核心 orchestration 自研，RAG 检索复用 LlamaIndex 的 `VectorStoreIndex` + retriever（避免重造轮子）。
6. **混合：自研核心 + LangGraph 仅 agent 部分** — 主 pipeline 自研，P5a chat agent 用 LangGraph 代替 Claude Agent SDK。

## Decision

**Chosen: TODO** — 待你确认或调整

我建议：**Option 5（自研核心 + LlamaIndex 仅 retrieval）**

理由（如同意则覆盖到 Decision 主体）：
- 项目规模小（~2000 行核心代码估算），不需要框架抽象
- 自研让每行代码都能讲清楚 → review最大优势
- LlamaIndex 的 retrieval 组件成熟（`VectorStoreIndex` + retriever + reranker），自己写不如复用
- P5a chat agent 用 Claude Agent SDK（per ADR-0006），与 pipeline 完全解耦
- 不引入 LangChain → 避免 breaking change 风险

### Why this option

TODO

### Why not the others

| Option | Reason rejected |
|--------|-----------------|
| 1 (LangChain 全家桶) | TODO（建议：抽象重、breaking change 风险、2026 年使用 = 落后信号） |
| 2 (LangGraph) | TODO（建议：用于本 pipeline 过重；P5a chat agent 用 Claude Agent SDK 更合适） |
| 3 (LlamaIndex 全家桶) | TODO（建议：chat agent 能力弱；P5a 需 Claude Agent SDK） |
| 4 (完全自研，含 RAG) | TODO（建议：重造 retrieval 轮子，时间收益不划算） |
| 6 (自研 + LangGraph) | TODO（建议：P5a 已定 Claude Agent SDK，无需 LangGraph） |

## Consequences

### Positive
TODO（建议）：
- 核心 orchestration 每行代码可解释，review可逐行讲
- LlamaIndex retrieval 成熟，节省 P2/P3 时间
- 不锁死，未来需求变化可只换替 retrieval 层
- 与 P5a chat agent（Claude Agent SDK）解耦

### Negative / Accepted Tradeoffs
TODO（建议）：
- 自研意味着错误处理、retry、并发控制都要自己写（~200-300 行）
- LlamaIndex 仍有依赖管理负担（版本兼容）
- 后续如需切到 LangChain 风格的 chain composition，需重构

### Mitigations
TODO

## Confirmation

- **怎么知道这个决策对了**：TODO（建议）：P2 W6 复盘时，能给完整 pipeline 画 sequence diagram，且每个组件代码 < 100 行
- **什么时候回头看**：TODO（建议）：P3 W10 末 — 若 10 类目实现导致代码超 3000 行，考虑重构

## References

- 内部：[ADR-0001](ADR-0001-llm-selection.md), [ADR-0002](ADR-0002-vector-db-embedding.md), [ADR-0006](ADR-0006-dual-system-architecture.md)
- 外部：
  - LangChain Anti-patterns（社区批评）
  - LlamaIndex 文档（仅看 retrieval 部分）
  - Anthropic *Building Effective Agents*
