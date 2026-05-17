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
| penalty_clause | ⏳ pending | - |
| service_period | ⏳ pending | - |
| working_hours | ⏳ pending | - |
| social_insurance | ⏳ pending | - |
| job_change_rights | ⏳ pending | - |
| non_compete | ⏳ pending | - |
| confidentiality_ip | ⏳ pending | - |
| termination | ⏳ pending | - |
| wage_composition | ⏳ pending | - |
