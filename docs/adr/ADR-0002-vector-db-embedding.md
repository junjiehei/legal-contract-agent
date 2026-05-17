# ADR-0002: Vector DB + Embedding Selection

**Status**: Draft
**Date**: TODO
**Deciders**: Dylan
**Related**: ADR-0001 (LLM Selection)

## Context

合同审查 pipeline 需要 RAG（Retrieval-Augmented Generation）支持：

- **法条检索**：当 agent 判断某条款违法时，需要从 7 部法律（劳动合同法/劳动法/社保法/实施条例/工资支付/女职工保护/司法解释）中检索具体法条作引用
- **判例检索**（P3 起）：当某些复杂类目（如 non_compete）需要 few-shot 时，从典型案例库检索相似情形
- **embedding 模型**：把中文法律条款 / 合同条款转成向量

两类决策必须一起做（向量库的能力决定 embedding 模型的发挥空间）。

服务器已就位：腾讯云北京六区，Qdrant 1.18.0 容器已跑（P1-W1 已部署，存储 `/data/qdrant`），bge-large-zh-v1.5 已下载到 `/data/hf-cache`。这意味着默认路径就是 Qdrant + bge-large-zh，但本 ADR 仍需正式记录"为什么选这条路、放弃了什么"。

## Decision Drivers

按优先级：

1. **中文法律检索的混合搜索能力**：必须支持 BM25（稀疏）+ embedding（稠密）混合。法律检索特别依赖精确字面匹配（如"劳动合同法第19条第1款"），纯向量搜索找不到这种引用。
2. **元数据过滤**：按法律名、条款编号、修订年份、类目过滤检索结果。
3. **中文 embedding 质量**：默认英文 embedding 在中文上拉胯，需要中文专属或多语言模型。
4. **部署复杂度**：solo dev，能 Docker 一键起来最好，避免运维负担。
5. **国内访问性**：embedding 模型下载需要 hf-mirror 或国内镜像。

## Considered Options

### 向量库

1. **Chroma** — 易上手，Python-friendly。但生产口碑一般（稳定性历史问题），元数据过滤弱，**不原生支持 hybrid search**。
2. **Qdrant** — Rust 内核，生产口碑好，**1.7+ 原生支持 hybrid search**，元数据过滤强。Docker 一键部署。
3. **Milvus** — 企业级，分布式。Solo project 用法显得过度。运维复杂度较高。
4. **pgvector**（Postgres 扩展）— 若已有 Postgres，元数据和向量同库 JOIN 方便；但本项目无 Postgres，需新管 DB。
5. **Weaviate** — 功能丰富（含 graph、generative search 等），但 schema 复杂度高。
6. **FAISS** — 是库不是 DB，需自己搭周边（持久化、过滤、API），不适合作生产组件。

### Embedding 模型

A. **bge-large-zh-v1.5**（BAAI 智源）— 中文 SOTA 之一，1024 维，开源，可走 hf-mirror 下载。
B. **bge-m3**（BAAI 多语言）— 支持多语言 + 多粒度（dense/sparse/multi-vector），更新。
C. **text2vec-large-chinese** — 老牌中文模型，简单稳定但相对落后。
D. **OpenAI text-embedding-3-large** — 英文最强，中文表现下降，API 调用（不能离线）。
E. **智谱 Embedding-3 / 通义 Embedding** — 国内 API embedding，无需自托管。

## Decision

**Chosen: TODO** — 待你确认或调整

我建议：**Qdrant（向量库）+ bge-large-zh-v1.5（embedding）**

理由（如你认同则保留为 Decision 内容，不认同则覆盖）：
- Qdrant 原生 hybrid search 是法律检索的硬要求
- bge-large-zh-v1.5 在中文 retrieval benchmarks（C-MTEB）上稳定第一梯队
- 都已在服务器部署/下载，零额外搭建成本
- 后续若需升级，bge-m3 是平滑路径（同一组织出品 + 多功能模式）

### Why this option

TODO（如同意以上理由，加 2-3 条具体的）

### Why not the others

| Option | Reason rejected |
|--------|-----------------|
| Chroma | TODO（建议：缺 hybrid search + 元数据过滤弱） |
| Milvus | TODO（建议：solo project 过度） |
| pgvector | TODO（建议：本项目无 Postgres，新增维护成本） |
| Weaviate | TODO（建议：schema 复杂度高，本项目用不到 graph 功能） |
| FAISS | TODO（建议：是库不是 DB） |
| bge-m3 | TODO（建议：当前 v1.5 已够；m3 多功能模式 P3 可升级） |
| OpenAI/智谱 API embedding | TODO（建议：成本 + 离线能力 + vendor lock-in） |

## Consequences

### Positive
TODO（建议）：
- 原生 hybrid search 解决法律检索的"精确引用 + 语义相似"双需求
- 完全本地化部署，无 embedding API 调用费用
- 模型 + 向量库都在 /data 持久化，重启可恢复
- bge-large-zh 模型权重 1.3GB，加载占 RAM ~2GB（与服务器 3.6G RAM 可容）

### Negative / Accepted Tradeoffs
TODO（建议）：
- bge-large-zh 推理需 CPU（无 GPU），单条 embedding ~50ms（可接受）
- Qdrant 运维需要自己维护（监控、备份、升级）
- 模型 + 向量库占 RAM ~3G，给业务代码留 600MB（紧但够）

### Mitigations
TODO

## Confirmation

- **怎么知道这个决策对了**：TODO（建议）：P3 阶段 hybrid search 在 eval 上比纯向量提升 ≥ 10% recall@5
- **什么时候回头看**：TODO（建议）：P4 cost benchmark 时；如发现 bge-large-zh CPU 推理成瓶颈，考虑 bge-m3 + GPU 或 API embedding

## References

- 内部：[ADR-0001](ADR-0001-llm-selection.md), [taxonomy.yaml](../taxonomy.yaml)
- 外部：
  - Qdrant Hybrid Search docs: https://qdrant.tech/articles/hybrid-search/
  - BAAI bge-large-zh-v1.5 模型卡: https://hf-mirror.com/BAAI/bge-large-zh-v1.5
  - C-MTEB（Chinese Massive Text Embedding Benchmark）leaderboard
