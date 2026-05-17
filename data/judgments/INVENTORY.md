# 裁判文书 / 案件 资产清单

**状态（2026-05-17）**：清空。

## 历史决策记录

### 尝试 1：fuzi-mingcha case_retrieval（已废弃）

- **数据源**：[SDUIRLab/fuzi-mingcha-v1_0-data](https://hf-mirror.com/datasets/SDUIRLab/fuzi-mingcha-v1_0-data)
- **采集**：2026-05-17，通过 hf-mirror 拉取 172MB 的 `case_retrieval/new_candidates.jsonl`
- **筛选**：v2 关键词过滤（劳动指示词 + taxonomy 关键词），得 56 份案件
- **质量验证**：抽查 `termination_001` 发现是刑事案件（敲诈勒索），关键词"辞退"只是背景出现
- **加严过滤尝试**：v3/v4 严过滤（要求民事标记词、剔除刑事判决词）→ 召回崩塌（0 / 1 份）
- **根因**：数据集本身偏刑事，劳动占比低，纯关键词无法精准识别
- **决定（2026-05-17 晚）**：删除全部 56 份。理由：
  1. 质量不达标，留着会污染 P2 单类目纵向打通的预期
  2. 已被 200 条高质量合成 eval data 替代（`eval/labeled/*.jsonl`）
  3. 真要补判例库，用官方"典型案例"（人社部/最高法/各地高院）30-50 份足够 RAG 用

## 未来恢复策略

若 P3-W8 RAG 阶段确需判例知识库：
1. 从 court.gov.cn / 人社部 / 最高法官网手动精选 30-50 份**官方典型案例**
2. 每份案件需含：争议条款 + 法院判定 + 适用法律 + 经济补偿数额（用作 RAG few-shot）
3. 重点覆盖 termination / non_compete / probation_period / social_insurance 四个高频类目

## 当前架构 — 判例库的替代品

- **RAG 知识库**：仅法律法规（`data/laws/`），P2 起足够
- **Eval ground truth**：200 条合成数据（`eval/labeled/`）
- **判例**：暂缺，必要时按上述策略补
