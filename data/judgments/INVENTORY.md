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


## ⚠️ 质量警告 (2026-05-17 抽查发现)

抽查 `termination_001.json` 发现是一例**敲诈勒索刑事案件**，关键词"辞退"只是背景信息。
说明当前 56 份案件存在**刑事-劳动误标**问题。

**根因**：fuzi-mingcha 的 case_retrieval 数据集本质是综合（多刑事少劳动），
单纯关键词过滤无法准确剔除"提及劳动但本质刑事"的案例。试过 v3/v4 严格过滤
（要求民事标记词、剔除刑事判决词），但分别得 0 和 1 个有效案例，召回崩塌。

**当前状态**：保留 v2 的 56 份作为占位，标记 `quality=mixed`。

**下一步处理（待用户决策）**：
1. 接受现状，仅用作 "case-style example" 起占位作用，不计入 eval ground truth
2. 切换到 [gehits/Chinese-Legal-Case-Classification-Dataset](https://hf-mirror.com/datasets/gehits/Chinese-Legal-Case-Classification-Dataset)
   —— 它有明确的"劳动人事"类目标签，质量信号更强（但是 Q&A 形式不是判决书）
3. 从 court.gov.cn 公开判例库手动精选 30-50 份核心类目案例（覆盖最关键的 termination / 
   non_compete / probation_period / social_insurance），数量少但质量高
4. P3-W8 之前再决定，现在不阻塞 P2 单类目纵向打通（probation_period 那条流水线
   不依赖判例 RAG，靠 prompt + 规则即可）

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
