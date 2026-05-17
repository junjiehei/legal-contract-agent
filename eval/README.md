# Eval Labeled Data

## 目的

每个 taxonomy 类目（共 10 个）配套一份 `.jsonl` 文件，作为 `agent vs ground-truth` 评测的标准答案。

## 文件结构

`eval/labeled/{category}.jsonl` — 每行一个 JSON 对象，UTF-8 编码。

每个类目目标 **20 条**：
- ~10 条 `violation_clear`（清晰违法）
- ~5-7 条 `compliant`（清晰合规）
- ~2-3 条 `borderline`（边界/争议案例）
- 偶尔 `violation_subtle`（违法但容易漏判）

10 个类目共 **200 条**。

## Schema

```json
{
  "id": "category_NNN",
  "clause": "原始合同条款（中文）",
  "context": "可选的上下文（哪种合同/哪部分/相关参数如最低工资）",
  "expected": {
    "violation": true | false,
    "category": "<taxonomy_id>",
    "violated_law": ["劳动合同法第X条第Y款", ...],
    "reason": "为什么违法/为什么合规（中文，2-4 句）",
    "severity": "high | medium | low | none",
    "suggestion": "修改建议（若 violation=true）"
  },
  "variation_type": "violation_clear | violation_subtle | compliant | borderline",
  "generated_by": "<who/what generated>",
  "generated_date": "YYYY-MM-DD",
  "notes": "可选注释，特别对 borderline 解释"
}
```

## 生成方法

由 Claude (Opus 4.7) 直接生成，**不**走外部 LLM API。理由：
1. Anthropic 模型在中文法律领域推理足够 — 经初版 prototype 抽查质量过关
2. 一致性高（同一模型同一上下文）
3. 不需 API key，不依赖网络
4. 生成过程可由用户在对话中实时审查 / 纠错

## 为什么 generated_by 不是 DeepSeek（项目主力 LLM）？

**eval 数据的生成模型 应当 ≠ 被评测模型**（避免自评偏差）。
- 生产：DeepSeek V3 / R1（per ADR-0001）
- Eval 标注：Claude Opus 4.7（本目录数据）

这种"评测员 ≠ 被试"的设置在 LLM evaluation 文献里是常规做法。

## 质量保证

每条样本上线前经过：
1. **自动检查**：法律引用格式正则、字段完整性、JSON valid
2. **人工抽检**：用户每类目抽 3-5 条审查
3. **二审循环**：发现错误 → 标注 `notes` 字段 + 修正后重新发布

如发现某条样本有误，**不要直接改**，而是 append 一条修正版（id 加 `_v2`），保留历史可追溯。

## 局限性

- 这些是**合成 eval 数据**，不是真实判决书或仲裁案例
- 部分 borderline 案例可能在不同法院 / 地区有不同裁判倾向
- 数字（如最低工资）截至 2026-05-17，未来需更新

## 当前进度

| 类目 | 状态 | 文件 |
|------|------|------|
| probation_period | ✅ 20 | `probation_period.jsonl` |
| penalty_clause | ✅ 20 | `penalty_clause.jsonl` |
| service_period | ✅ 20 | `service_period.jsonl` |
| working_hours | ✅ 20 | `working_hours.jsonl` |
| social_insurance | ✅ 20 | `social_insurance.jsonl` |
| job_change_rights | ✅ 20 | `job_change_rights.jsonl` |
| non_compete | ✅ 20 | `non_compete.jsonl` |
| confidentiality_ip | ✅ 20 | `confidentiality_ip.jsonl` |
| termination | ✅ 20 | `termination.jsonl` |
| wage_composition | ✅ 20 | `wage_composition.jsonl` |

**总计：200 条，10/10 类目完成。**

## 抽查建议

由于全部 200 条由 Claude 一次性生成，难免有错。建议用户在 P1-W3 前完成：
- 每个类目随机抽 3-5 条人工核对
- 重点检查 `borderline` 类目（法律解释最容易出错）
- 发现错误的样本 id 反馈，由生成者（Claude）出修正版 `_v2`

## 未来扩展

- v2 添加 `region` 字段（不同地区最低工资、社平工资差异）
- v3 添加 `case_law_reference` 字段（关联典型判例）
- v4 增加 `synthetic_contract` 维度（多条款合并的完整合同测试 agent 端到端能力）
