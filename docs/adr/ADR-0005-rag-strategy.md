# ADR-0005: RAG Strategy — Sparse / Dense / Hybrid / Re-rank

**Status**: Draft (defer until P3 W8)
**Date**: TODO
**Deciders**: Dylan
**Related**: ADR-0002 (Vector DB), ADR-0003 (Orchestration)

## Context

合同审查 agent 在判断违法时，需要从 7 部法律 + （可能的）判例库中检索相关法条/案例作为引用依据。这是 RAG 系统的核心。

**为什么这个 ADR 等到 P3 W8 写**：现在（P1 末）对真实检索质量没有数据。P2 单类目跑通后，会得到第一批 retrieval 表现数据；P3 横向铺开时检索质量成为瓶颈。届时才能基于数据决策，不是凭空猜。

**当前状态**：P1 末，Qdrant + bge-large-zh 已部署（per ADR-0002），但具体检索策略未定。

## Decision Drivers

按优先级：

1. **法条引用精确度**：用户期望"违反劳动合同法第19条第1款"这种精确引用，**幻觉一次=信任崩塌**。检索必须能找到正确的法条。
2. **中文法律语义理解**：合同条款用词 vs 法条用词常不同（如合同写"试用期不超过 4 个月" vs 法条说"试用期不得超过 1 个月" — 关键的是"超过法定"，不是字面相似）。
3. **延迟预算**：每次审查总延迟控制在 P95 < 5s（per taxonomy.yaml 各 strategy）。retrieval 不能成瓶颈。
4. **混合策略复杂度**：Hybrid + re-rank 比纯 dense 多 1-2 个组件，运维和 debug 复杂度上升。值不值？
5. **未来扩展**：判例库（typical cases）加入后，检索粒度和召回策略可能需要重新设计。

## Considered Options

### 检索策略

1. **Pure dense（仅 embedding）** — 全向量检索。简单。但找不到精确法条编号（"第19条"这种字面引用）。
2. **Pure sparse（仅 BM25）** — 全词频检索。精确但缺乏语义。"试用期超期" 检索 不到没用过这个词的相关法条。
3. **Hybrid（dense + sparse 双路融合）** — Qdrant 1.7+ 原生支持。两路各取 top-K，分数加权融合（RRF 或线性加权）。
4. **Hybrid + cross-encoder re-rank** — 在 Hybrid 检索的 top-N 上用 cross-encoder（如 bge-reranker-large）重排，提升 top-K 精度。
5. **Hybrid + LLM re-rank** — 用 LLM（如 DeepSeek-V3）做 listwise re-ranking。更贵但更智能。
6. **Multi-stage with HyDE**（Hypothetical Document Embeddings）— 先让 LLM 根据 query 生成"假设的相关文档"，再用其 embedding 检索。对长 query 效果好但增加 LLM 调用。
7. **Multi-vector / late interaction（ColBERT 风格）** — 多 token-level embedding，性能强但部署复杂。

### 切分策略（chunk granularity）

A. **按章（粗）** — 每章一个 chunk。语义完整但召回精度低。
B. **按条（中）** — 每条一个 chunk。**对法律最自然的粒度**。
C. **按段（细）** — 每段一个 chunk。可能过细，丢失上下文。
D. **滑动窗口** — overlap 切分。机械但稳定。

## Decision

**Chosen: TODO** — 等 P3 W8 基于实测数据决定

我**初步建议**（P3 决策前的 hypothesis）：

- **检索策略**：Option 4 — **Hybrid（dense + sparse）+ bge-reranker-large 重排**
- **切分粒度**：Option B — 按条（第X条作为一个 chunk）

理由（暂定，待 P3 验证）：
- Hybrid 解决"精确引用 + 语义相似"双需求（法律检索的硬要求）
- Cross-encoder re-rank 比 LLM re-rank 便宜 10×，精度接近
- 按条切分 = 法律最自然结构 + 每个 chunk 自带"条号"元数据便于引用

### Why this option

TODO（P3 W8 数据出来后填）

### Why not the others

| Option | Reason rejected |
|--------|-----------------|
| Pure dense | TODO（建议：丢失精确字面引用能力） |
| Pure sparse | TODO（建议：缺乏语义理解） |
| Hybrid + LLM re-rank | TODO（建议：cost 比 cross-encoder 高 10×，精度接近） |
| HyDE | TODO（建议：合同审查的 query 较短，HyDE 价值不大） |
| Multi-vector / ColBERT | TODO（建议：部署复杂，超出 solo dev 能力范围） |
| 按章切分 | TODO（建议：粒度过粗，召回精度低） |
| 按段切分 | TODO（建议：过细，丢失条款上下文） |
| 滑动窗口 | TODO（建议：法律有天然章/条结构，机械窗口失去这个优势） |

## Consequences

### Positive
TODO（待数据出来填）：
- 预期：法条引用精度 ≥ 95%（top-3 retrieval 包含正确法条）
- ...

### Negative / Accepted Tradeoffs
TODO

### Mitigations
TODO

## Confirmation

- **怎么知道这个决策对了**：TODO（建议）：
  - **检索 eval**：人工标注 50 个 (query, golden_law_articles) pair，测 retrieval recall@5 ≥ 0.95
  - **端到端 eval**：在 200 条 eval 样本上，agent 引用的法条与 expected.violated_law 匹配率 ≥ 0.90
- **什么时候回头看**：TODO（建议）：P3 W10 中期；P4 W11 失败分析时
- **触发重新评估**：retrieval recall@5 < 0.90 持续 1 周，重新评估切分或检索策略

## References

- 内部：[ADR-0002](ADR-0002-vector-db-embedding.md), [taxonomy.yaml](../taxonomy.yaml)
- 外部：
  - Hybrid Search 文献综述（如 Anthropic 的 "Introducing Contextual Retrieval"）
  - Qdrant Hybrid Search docs
  - BGE Reranker 模型卡: https://hf-mirror.com/BAAI/bge-reranker-large
  - HyDE 论文（如不采用，引用作为对比基准）
