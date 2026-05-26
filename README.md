# 劳动合同阅读辅助

一个**供个人阅读劳动合同时参考**的辅助工具：尝试标注一些可能值得多看一眼的条款，并附上相关法律条文。**仅供参考，不构成法律意见，也不替代律师。**

> **本工具不构成法律意见**。所有结论由 AI 生成，仅供参考；重要决策请咨询律师。详见 [DISCLAIMER](docs/DISCLAIMER.md)。

## 现状

项目处于**设计 + 早期实现**阶段，尚未对外开放。目前主要在做：

- 架构设计文档（成型中）
- Ingestion 流水线 6 模块（设计完成，待编码）
- 评测集（200 条合成样本，10 类目 × 20）
- 法律条文采集（劳动相关 7 部）

准确率和功能都在迭代，**不建议直接用于真实重要决策**。

## 文档

| 文档 | 内容 |
|------|------|
| [docs/HLD.md](docs/HLD.md) | 总体架构（6 层 + 跨层关切） |
| [docs/SYSTEM1_PIPELINE.md](docs/SYSTEM1_PIPELINE.md) | 合同处理流水线的实现级设计 |
| [docs/SYSTEM2_CHAT_AGENT.md](docs/SYSTEM2_CHAT_AGENT.md) | 对话式 agent（骨架，P5 才动） |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 组件交互 / 数据流 / 序列图 |
| [docs/EVAL_QA.md](docs/EVAL_QA.md) | 评测与质量保障 |
| [docs/SECURITY_COMPLIANCE.md](docs/SECURITY_COMPLIANCE.md) | 数据安全 + AI 合规 + 责任划分 |
| [docs/DEPLOYMENT_OPS.md](docs/DEPLOYMENT_OPS.md) | 部署模式（含私有化） |
| [docs/taxonomy.yaml](docs/taxonomy.yaml) | 10 风险类目 |
| [docs/adr/](docs/adr/) | 关键决策记录 |
| [docs/DISCLAIMER.md](docs/DISCLAIMER.md) | 免责声明 |

## 大致做法（详见上面的文档）

- 双系统：一个确定性的处理流水线（System 1，P2–P4）+ 之后的对话式辅助（System 2，P5）。
- 流水线分阶段：入料 → 解析 → 切条款 → 检测 → 复核 → 出报告；每条结论尽量带法律条文出处。
- 多模态输入按需走 OCR / VLM（P3 起），还在评估中。
- 立场上**依法中立**，产品体验**优先服务劳动者**——但不替代律师。

## 技术栈（仍可能调整）

| 层 | 当前选型 | 备注 |
|----|---------|------|
| Language | Python 3.10+ | |
| LLM | DeepSeek V3 / R1 | 接口抽象、可切其他 provider |
| Embedding | bge-large-zh-v1.5 | 中文常用 |
| Vector DB | Qdrant | |
| PDF 解析 | pdfplumber（MIT） | 许可证宽松；pypdf 仅用于廉价格式探测 |
| OCR / VLM | PaddleOCR / Qwen-VL | P3 起 |
| 前端 | FastAPI + HTMX | P4 起；服务端渲染，便于私有部署 |
| 编排 | 自研最小化 + LlamaIndex（仅检索部分） | 不全栈框架化 |

更多决策见 [`docs/adr/`](docs/adr/)。

## 大致时间表

| 阶段 | 时间 | 干啥 |
|------|------|------|
| P1 | 5/17–6/8 | 数据 + 类目 + 评测骨架（已就位） |
| P2 | 6/9–6/29 | 流水线打通（部分类目） |
| P3 | 6/30–7/27 | 全类目 + RAG + 多模态 |
| P4 | 7/28–8/24 | 评测打磨 + 前端 + MCP |
| P5 | 8/25–8/31 | 对话 agent + 部署与文档 |

各阶段都可能调整或推迟，节奏先做精再扩。

## 运行中的服务

| 服务 | 状态 | 端口 |
|------|------|------|
| Qdrant 向量库 | 运行中（Docker） | 6333 / 6334 |

## 局限

- 评测集是 LLM 合成数据 + 人工抽检，不是真实判决书或仲裁案例。
- 法律条文截至 2026-05；法律会修订，结论需对照最新版本核实。
- 准确率仍在爬坡，复杂或边界案例倾向于"标低置信、建议人工复核"。
- 努力依法中立、优先服务劳动者，但**不替代律师**。

## License

[Apache-2.0](LICENSE)。
