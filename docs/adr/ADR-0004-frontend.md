# ADR-0004: Frontend — Streamlit vs Next.js vs CLI

**Status**: Draft (defer until P4 前)
**Date**: TODO
**Deciders**: Dylan
**Related**: ADR-0006 (Dual System Architecture)

## Context

项目需要一个**可视化界面**用于：

1. **演示**：review 时展示 agent 工作过程（上传合同 → 显示风险标注 → 引用法条 → 给建议）
2. **交互（次要）**：用户上传合同、查看结果、下载报告
3. **录屏 demo 视频**（P5b）的视觉载体

**关键约束**：
- 项目核心价值在 backend / AI architecture，**前端不是评判维度**
- Solo dev 时间预算约 150-225 小时，前端不应占超过 10%
- P5b 才录 demo，所以前端 P4 后期再做也来得及
- Chat agent v2（P5a）若做了，可能不需要独立前端（在 Claude Code 里就能演示）

## Decision Drivers

按优先级：

1. **时间投入 ROI**（最高）：前端不是项目深度所在，投入要节制
2. **演示效果**：能清晰展示 pipeline 的关键 UX（条款标注、法条引用、严重度分级）
3. **学习成本**：solo dev 已分散投入在 backend + agent + 法律领域；前端不应再增学习负担
4. **可录屏性**：demo 视频需要流畅的交互
5. **个人技能匹配**：你之前的前端经验深度（**TODO 你自己评估**）

## Considered Options

1. **Streamlit** — Python-native，1-2 天可做完。界面"有 ML demo 感"。适合快速可用。
2. **Gradio** — 类似 Streamlit，更偏 ML demo。Hugging Face Spaces 生态。
3. **Next.js + Tailwind + shadcn/ui** — 现代、polished，但 2-3 周。需要 React 熟悉度。
4. **HTML + HTMX + 后端模板** — 轻量、快速，但视觉不够现代。
5. **CLI only**（不做前端）— 全部命令行 + 输出 JSON / markdown 报告。演示靠 terminal screencast。
6. **跳过独立前端，复用 Claude Code 作为前端** — pipeline 暴露为 MCP server，用户在 Claude Code 里调用。P5a 的 chat agent 也用类似方式。

## Decision

**Chosen: TODO** — 待你 P4 时确认（现在 P1 末，不需要锁定）

我建议：**Streamlit**（option 1）作 baseline；若 P5a chat agent 做出来后效果好，**前端实际由 chat agent 承担**（option 6 + Streamlit 备用）

理由（如同意则覆盖）：
- Streamlit 1 天可起，是不阻塞 P5b 叙事的最快选项
- 前端不是项目核心价值；审查者关注的是后端架构和 eval 严谨度
- 省下的时间投入到 P4 eval 优化或 P5b 架构文档
- Chat agent v2 + MCP server 已经是强 demo，前端可能变成"加分项"而非"必要项"

### Why this option

TODO

### Why not the others

| Option | Reason rejected |
|--------|-----------------|
| Gradio | TODO（建议：与 Streamlit 类似但 ML-demo 味更重；选 Streamlit 因更通用） |
| Next.js + Tailwind + shadcn | TODO（建议：时间 ROI 不划算；除非你 React 已熟） |
| HTML + HTMX | TODO（建议：视觉不够现代，2026 review场景下不加分） |
| CLI only | TODO（建议：录 demo 视频时缺乏视觉冲击力） |
| 全部 Claude Code（无独立 UI） | TODO（建议：作为 fallback 而非主选；用户可能没装 Claude Code） |

## Consequences

### Positive
TODO（建议）：
- 1-2 天前端时间预算，省出时间投到 eval 优化
- Streamlit 与 Python 生态无缝（直接 import pipeline 模块）
- 录屏友好（Streamlit 默认 layout 干净）

### Negative / Accepted Tradeoffs
TODO（建议）：
- Streamlit "ML demo 感" — 审查者可能认为不像生产产品
- 缺乏精细的样式控制（无法做 inline 高亮、tooltip 等高级交互）
- 多用户/状态管理弱（但本项目无需）

### Mitigations
TODO（建议）：
- 在架构文档中说明"前端非项目核心，故选最小可用方案"
- 录 demo 时强调 backend 的 pipeline 流程而非 UI 美观

## Confirmation

- **怎么知道这个决策对了**：TODO（建议）：P5b demo 视频拍出来流畅，审查者未对前端提出负面问题
- **什么时候回头看**：TODO（建议）：P4 W13 — 若 chat agent v2 进度顺利且演示力强，前端可降级为可选

## References

- 内部：[ADR-0006](ADR-0006-dual-system-architecture.md)（chat agent 已是主要 demo 载体）
- 外部：
  - Streamlit 文档
  - shadcn/ui examples
