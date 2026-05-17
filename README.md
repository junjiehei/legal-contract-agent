# 中国劳动合同审查 Agent

面向劳动者的 AI 合同审查系统：识别违法/不利条款、引用相关法条、给出修改建议。

## 状态

W1（2026-05-17 起）— Foundation phase：数据采集 + Taxonomy 验证 + Eval 骨架。

## 项目导航

| 路径 | 用途 |
|------|------|
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

- **P1 奠基** 5/19–6/8（提前到 5/17 起）— 数据 + Taxonomy + Eval 骨架
- **P2 纵向打通** 6/9–6/29 — Pipeline 单类目，引入 Tool Use + LLMClient
- **P3 横向铺开** 6/30–7/27 — Pipeline 全 10 类目 + RAG 成熟
- **P4 深度打磨** 7/28–8/24 — Eval 驱动改进 + 性能 + MCP server 包装
- **P5a Chat Agent v2** 8/25–8/28 — Skills + Memory + Sub-agents + MCP client（基于 Claude Agent SDK）
- **P5b 叙事 + 面试准备** 8/29–8/31 — 架构文档 + Demo + 面试题准备

## 双系统架构（详见 ADR-0006）

| 系统 | 风格 | 时序 | 角色 |
|------|------|------|------|
| Pipeline（合同审查） | workflow | P2-P4 | 确定性 detection；P4 末包装为 MCP server |
| Chat Agent v2（法律咨询） | agent loop | P5a | 限定 10 taxonomy 类目；通过 MCP client 调用 pipeline |
