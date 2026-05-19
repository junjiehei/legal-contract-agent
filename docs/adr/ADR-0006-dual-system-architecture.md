# ADR-0006: Dual System Architecture — Pipeline + Chat Agent

**Status**: Proposed
**Date**: 2026-05-18
**Deciders**: Dylan
**Related**: ADR-0001 (LLM Selection)

## Context

P1 W1 收尾时（2026-05-18），项目原定为单一确定性合同审查 pipeline（覆盖 10 个 taxonomy 类目）。重新评估后决定扩展为**双系统架构**：

1. 主系统：合同审查 pipeline（workflow 风格）— 现有计划
2. 子系统：法律咨询 chat agent（agent loop 风格）— 新增

驱动重新评估的原因：

- **review需求**：2026 年单纯 RAG pipeline 已不足以体现"跟得上业界" — MCP / Skills / Memory / Sub-agents 是当前审查者期待看到的技术
- **产品互补**：合同审查（一次性结构化输入）+ 法律咨询（持续对话）能覆盖更完整的劳动者需求场景
- **技术深度学习**：用户希望在真实项目中应用 2026 主流 agent 技术，而不是看教程

## Decision Drivers

按优先级：

1. **不破坏 P2-P4 主线进度** — pipeline 是项目的根基，必须先稳
2. 覆盖广度（覆盖 2026 主流 agent 技术）
3. 产品用户场景覆盖
4. 避免"用了 N 个技术但都浅尝辄止"的反效果

## Considered Options

1. **单系统（pipeline only）** — 仅做合同审查 workflow，不涉及 chat agent
2. **单系统（chat agent only）** — 把合同审查也实现为 chat agent 内的 skill
3. **混合系统** — pipeline + chat agent 通过 MCP 集成 ← **选定**
4. **完全分离** — 两个独立项目，无集成层

## Decision

**Chosen: Option 3 — Pipeline + Chat Agent，通过 MCP 集成**

### 架构

```
┌─────────────────────────────────────────────────────────┐
│  System 1: Contract Review Pipeline (P2-P4)            │
│  ─ workflow 风格，10 taxonomy 类目                       │
│  ─ Tool Use + LLMClient + RAG + Verifier               │
│  ─ P4 末：包装为 MCP server                              │
└─────────────────────────────────────────────────────────┘
                         ↑
                    MCP protocol
                         ↑
┌─────────────────────────────────────────────────────────┐
│  System 2: Chat Agent v2 (P5a)                         │
│  ─ agent loop 风格                                      │
│  ─ Claude Agent SDK 作 harness                          │
│  ─ Skills: 3-5 个 (审查/试用期/加班费/社保/补偿)         │
│  ─ Memory: 跨会话用户上下文                              │
│  ─ Sub-agents: 复杂查询分解                              │
│  ─ MCP client: 调用 System 1                            │
│  ─ 范围严格限定: 10 taxonomy 相关问题                    │
└─────────────────────────────────────────────────────────┘
```

### 时序（与项目五阶段对齐）

| Phase | Pipeline 任务 | Chat Agent 任务 |
|-------|--------------|----------------|
| P2 (6/9-6/29) | 单类目纵向打通；引入 Tool Use + LLMClient | （不动）|
| P3 (6/30-7/27) | 横向铺开 10 类目 + RAG 成熟 | （不动）|
| P4 (7/28-8/24) | Eval 打磨 + 性能 + observability；末期包装为 MCP server | （不动）|
| P5a (8/25-8/28) | （冻结）| 启动：Claude Agent SDK + Skills + Memory + Sub-agents + MCP client |
| P5b (8/29-8/31) | （冻结）| 架构文档 + Demo + review准备 |

### Why this option

1. **架构边界清晰**：pipeline 是确定性的（eval 信号干净），chat agent 是开放的（灵活但 eval 难度高）。两者职责清晰，可独立 eval 和优化。

2. **MCP 集成是关键 wow factor**：在 Claude Code 里能直接调用我们的合同审查 = 强 demo。同时这种"agent ecosystem"叙事在 2026 review中很有杀伤力。

3. **scope 可控**：chat agent 限定在 10 taxonomy 类目相关问题，不做通用法律咨询。eval 复用 200 条样本 + 加 30-50 条对话样本。

4. **失败回退路径明确**：若 P5a 时间不够，chat agent 降级为"在 Claude Code 内以 skill 形式调用 pipeline"，仍保留 demo value（不会因为 chat agent 没做好而损失 pipeline 成果）。

### Why not the others

| Option | Reason rejected |
|--------|-----------------|
| 1 (pipeline only) | 2026 review要求 agent 技术信号，单 pipeline 缺乏"跟得上业界"的证据 |
| 2 (chat agent only) | 合同审查是结构化确定性任务，强行做成 agent loop 会破坏 eval 信号 4 倍以上 |
| 4 (完全分离) | 失去 MCP 集成的 wow factor，无法讲"两系统互通"的架构叙事 |

## Consequences

### Positive

- 完整覆盖 2026 主流 agent 技术（Tool Use, MCP server/client, Skills, Memory, Sub-agents, Harness）
- Pipeline 和 chat agent 各自采用最优架构（workflow vs agent loop）
- review叙事强：能讲清楚"workflow vs agent 的取舍 + 两者通过 MCP 集成"
- 产品扩展性：未来新增 skill 不影响 pipeline 稳定性

### Negative / Accepted Tradeoffs

- 项目复杂度上升（两个子系统 + 集成层）
- P5 阶段时间紧（chat agent 4 天 + 叙事 3 天）
- chat agent eval 需要独立设计（开放 Q&A 比结构化 detection 难评测）
- 维护成本翻倍（两套 prompt + 两套依赖 + 两套部署）

### Mitigations

- **硬规则：P4 W14 末才启动 chat agent**（pipeline 10 类目 P≥0.85 R≥0.8 是前置条件）
- **scope 硬约束**：chat agent 不做通用法律咨询，严格限定 10 类目相关
- **预定义降级方案**：P5a 超期 → chat agent 退化为单一 Claude Code skill 调用 pipeline MCP server
- chat agent eval 设计：复用 200 条 + 加 30-50 条对话样本，不重新搞独立 eval 体系

## Confirmation

- **P4 W14 末通过条件**：pipeline 10 类目全 P≥0.85 R≥0.80 → 才允许启动 P5a 的 chat agent
- **P5a 通过条件**：chat agent 能在 Claude Code 里被发现并调用 + 至少 3 个 skill 可工作 + Memory 跨会话验证通过
- **触发降级的条件**：P4 W14 末 pipeline 仍不达标 → P5a 直接进入降级方案（单 skill wrapper）
- **回头改的条件**：若用户测试反馈 chat agent 实际价值低（如 70% 查询不在 10 类目范围内），P5 后期可调整为强化 pipeline + 简化 chat agent

## References

- 内部：[ADR-0001](ADR-0001-llm-selection.md), ADR-0002 (Vector DB, pending), ADR-0003 (Orchestration, pending)
- Anthropic: [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — workflow vs agent 区分
- MCP spec: https://modelcontextprotocol.io
- Claude Agent SDK 文档
