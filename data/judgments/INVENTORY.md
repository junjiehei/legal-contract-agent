# 裁判文书 / 案件 资产清单

> ⚠️ **重要说明**：此处的数据**不是从裁判文书网直接抓取的原始判决书**，而是从 [SDUIRLab/fuzi-mingcha](https://hf-mirror.com/datasets/SDUIRLab/fuzi-mingcha-v1_0-data) 法律 LLM 训练集中筛出来的劳动相关案件片段（case facts + 律师分析 Q&A）。
>
> **为什么用这个**：国内裁判文书网原始判决书的合法批量获取在 2026 年仍然困难；fuzi-mingcha 是公开 CC 协议的法律 LLM 数据集，内容来源最终都是裁判文书网，质量足够支撑我们的 taxonomy detection eval。
>
> **下游使用**：可直接作为 eval set 的种子和 RAG 的判例知识库。P4 阶段如果需要 forensic-grade 真原始判决书，再单独通过 court.gov.cn / 学术合作获取。

- 数据集来源：SDUIRLab/fuzi-mingcha-v1_0-data
  - case_retrieval/new_candidates.jsonl (案件 facts)
  - lawyerllama/lawyer_llama_4analyse_v1.jsonl (律师案件分析)
  - lawyerllama/lawyer_llama_4answer_v1.jsonl (律师答疑)
- 采集日期：2026-05-17
- 自动筛选：劳动指示词 + taxonomy 关键词分类
- 文件数：56

## 按类目分布

| 类目 | 实际 | 目标 | 状态 |
|------|-----:|-----:|------|
| `probation_period` | 1 | 10 | ⚠️ 不足 |
| `non_compete` | 0 | 15 | ⚠️ 不足 |
| `penalty_clause` | 4 | 10 | ⚠️ 不足 |
| `service_period` | 3 | 8 | ⚠️ 不足 |
| `working_hours` | 10 | 10 | ✅ |
| `wage_composition` | 6 | 10 | ⚠️ 不足 |
| `social_insurance` | 12 | 12 | ✅ |
| `termination` | 15 | 15 | ✅ |
| `job_change_rights` | 0 | 5 | ⚠️ 不足 |
| `confidentiality_ip` | 5 | 5 | ✅ |

## 备注

- 部分类目（如 `non_compete`、`social_insurance`、`probation_period`）样本可能不足，因为 fuzi-mingcha 数据集偏刑事/民事综合，劳动专项数据相对少。
- P3-W8 之前如果某些类目 eval set 不够，可考虑：
  1. 从 court.gov.cn 公开判例库手动补充该类目的案例
  2. 用现有案例做 augmentation（让 LLM 生成同类目的合成案例）
  3. 接受现有覆盖度，在 ADR 里明确记录这个 limitation
