# Architecture Decision Records

本目录记录所有关键架构决策。每个决策一个文件，命名 `ADR-NNNN-{slug}.md`。

## 为什么写 ADR

- **当下**：强迫自己想清楚 tradeoff，避免后悔
- **未来**：决策被推翻时知道原因（不是 reinvent the wheel）
- **review**：每篇 ADR 都是你"系统思考能力"的证据

## ADR 模板

```markdown
# ADR-{编号}: {决策标题}

**Status**: Proposed | Accepted | Deprecated | Superseded by ADR-XXXX
**Date**: YYYY-MM-DD
**Deciders**: {名字}

## Context

为什么现在要做这个决策？要解决什么问题？有哪些约束（技术/业务/时间/团队）？
2-4 句话讲清楚。

## Decision Drivers

驱动决策的核心因素（3-5 条，有优先级）：
- {因素1}
- {因素2}

## Considered Options

1. **Option A** — 一句话描述
2. **Option B** — 一句话描述
3. **Option C** — 一句话描述

至少 3 个，否则不是 trade-off 是单选题。

## Decision

**Chosen: Option X**

一句话表述决策本身。

### Why this option
- {为何最满足 drivers}

### Why not the others

| Option | Reason rejected |
|--------|-----------------|
| Option A | ... |
| Option B | ... |

## Consequences

### Positive
- 我们获得什么

### Negative / Accepted Tradeoffs
- 我们放弃/承担什么（**回避缺点的 ADR 一眼假**）

### Mitigations
- 如何管理风险

## Confirmation

- 怎么知道这个决策对了？看什么指标？
- 什么条件下回头改？

## References

- 相关链接、benchmark、其他 ADR
```

## 3 个常见坑

1. **写成"决策声明"而非"决策记录"** — 没有 alternatives 和 tradeoff 的 ADR 是简历，不是 ADR
2. **正面话讲过头** — 没有 Negative/Tradeoff 章节的 ADR 一眼假
3. **写完不维护** — 当决策被推翻：**新建一篇 ADR-XXXX 标记 "Supersedes ADR-NNNN"**，不要改老的

## 索引

| ID | 标题 | 状态 |
|----|------|------|
| [ADR-0001](ADR-0001-llm-selection.md) | LLM Provider Selection — DeepSeek as Primary | Accepted |
| [ADR-0002](ADR-0002-vector-db-embedding.md) | Vector DB + Embedding Selection | Draft (2026-05-18) |
| [ADR-0003](ADR-0003-orchestration.md) | Orchestration: Custom vs Framework | Draft (2026-05-18) |
| [ADR-0004](ADR-0004-frontend.md) | Frontend: Streamlit vs Next.js | **Superseded by ADR-0010** |
| [ADR-0005](ADR-0005-rag-strategy.md) | RAG Strategy: Hybrid + Re-rank | Draft (defer to P3 W8) |
| [ADR-0006](ADR-0006-dual-system-architecture.md) | Dual System Architecture (Pipeline + Chat Agent) | Proposed (2026-05-18) |
| [ADR-0007](ADR-0007-confidentiality.md) | Confidentiality Architecture | Proposed (2026-05-20) |
| [ADR-0008](ADR-0008-multimodal-input.md) | Multimodal Input Strategy | Proposed (2026-05-20) |
| [ADR-0009](ADR-0009-mcp-integration.md) | MCP Integration | Proposed (2026-05-20) |
| [ADR-0010](ADR-0010-frontend-revision.md) | Frontend Revision (Supersedes ADR-0004) | Proposed (2026-05-20) |
