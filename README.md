# 中国劳动合同审查 Agent

面向劳动者的 AI 合同审查系统：识别违法/不利条款、引用相关法条、给出修改建议。

> **⚠️ 本工具不构成法律意见**。所有 AI 输出仅供参考，重要决策须经持牌律师复核。详见 [`docs/DISCLAIMER.md`](docs/DISCLAIMER.md)。

## 状态

**P1 已完成（2026-05-18）** — 数据采集、Taxonomy v0.2、Eval 骨架（200 条 ground truth + harness + 3 baseline）。

当前等待 P2 启动（计划 2026-06-09）。

## 项目导航

| 路径 | 用途 |
|------|------|
| `docs/ARCHITECTURE.md` | **架构总览 + mermaid 图**（先读这个） |
| `docs/EVAL_GUIDE.md` | 评测体系详解（指标、阈值、baseline） |
| `docs/DISCLAIMER.md` | 免责声明（法律 AI 必读） |
| `data/INVENTORY.md` | 数据资产清单（**每次新增数据必须更新**） |
| `data/laws/MANIFEST.md` | 法律采集 checklist（W1 当前任务） |
| `docs/adr/` | 架构决策记录 |
| `eval/labeled/` | Ground truth 标注（P1-W3 起） |
| `src/` | 业务代码（P2 起） |
| `scripts/` | 采集和工具脚本 |



## 运行中的服务

| 服务 | 状态 | 端口 | 存储 |
|------|------|------|------|
| Qdrant 向量库 | running (Docker) | 6333 (HTTP), 6334 (gRPC) | `/data/qdrant` |

## 文档导航

**从这里开始**：[docs/HLD.md](docs/HLD.md) — 总体架构（6 层 + 跨层关切 + 演进路线）

| 文档 | 内容 |
|------|------|
| [docs/HLD.md](docs/HLD.md) | 总体架构设计（顶层视角）⭐ |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 详细组件交互 + 数据流 + 双系统 |
| [docs/EVAL_GUIDE.md](docs/EVAL_GUIDE.md) | 评测体系（指标 / 阈值 / baseline） |
| [docs/taxonomy.yaml](docs/taxonomy.yaml) | 10 风险类目 source of truth |
| [docs/DISCLAIMER.md](docs/DISCLAIMER.md) | 免责声明 |
| [docs/adr/](docs/adr/) | 架构决策记录（ADR-0001~0010） |
| [data/INVENTORY.md](data/INVENTORY.md) | 数据资产清单 |
| [eval/README.md](eval/README.md) | Eval 数据 schema |

## 技术栈

| 层 | 选型 | 备注 |
|----|------|------|
| Language | Python 3.11+ | |
| LLM | DeepSeek（V3 主力 + R1 推理） | LLMClient 抽象，可切 provider |
| Embedding | bge-large-zh-v1.5 | 中文 SOTA |
| Vector DB | Qdrant | hybrid search 必须 |
| Orchestration | 自研最小化 + LlamaIndex (retrieval 部分) | 不用 LangChain 全家桶 |
| Frontend | Streamlit | P4 才动手 |

详见 `docs/adr/`。

## 时间线

- **P1 奠基** 5/19–6/8（提前到 5/17 起）✅ 2026-05-18 完成— 数据 + Taxonomy + Eval 骨架
- **P2 纵向打通** 6/9–6/29 — Pipeline 单类目，引入 Tool Use + LLMClient
- **P3 横向铺开** 6/30–7/27 — Pipeline 全 10 类目 + RAG 成熟
- **P4 深度打磨** 7/28–8/24 — Eval 驱动改进 + 性能 + MCP server 包装
- **P5a Chat Agent v2** 8/25–8/28 — Skills + Memory + Sub-agents + MCP client（基于 Claude Agent SDK）
- **P5b 文档 + Demo 发布** 8/29–8/31 — 架构文档 + Demo + 文档归档

## 双系统架构（详见 ADR-0006）

| 系统 | 风格 | 时序 | 角色 |
|------|------|------|------|
| Pipeline（合同审查） | workflow | P2-P4 | 确定性 detection；P4 末包装为 MCP server |
| Chat Agent v2（法律咨询） | agent loop | P5a | 限定 10 taxonomy 类目；通过 MCP client 调用 pipeline |
