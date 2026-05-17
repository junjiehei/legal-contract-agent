"""Apply 15 cross-LLM spot-check corrections to eval JSONL files (2026-05-18).

User performed cross-validation with DeepSeek and GPT, identified 15 issues.
This script applies the corrections in-place. The script itself is preserved
in scripts/ as audit trail.

Corrections by category:
- confidentiality_ip: 1 (006)
- job_change_rights: 4 (014, 017, 019, 020)
- non_compete:       5 (004, 009, 016, 017, 020)
- penalty_clause:    3 (011, 012, 017)
- probation_period:  1 (017) -- legal substantive correction
- termination:       1 (007) -- removes abolished regulation citation

Two minor deviations from user's spec (confirmed with user):
- confidentiality_ip_006: violation field already False; only update other fields
- non_compete_009: schema has no "low-medium"; using "medium" instead
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


STAGING = Path(__file__).parent  # eval-staging/

CORRECTION_DATE = "2026-05-18"
CORRECTION_NOTE_SUFFIX = " [v2 corrected 2026-05-18 per cross-LLM check]"


def set_nested(obj: dict, path: str, value: Any) -> None:
    """Set obj[a][b][c] given path 'a.b.c'."""
    keys = path.split(".")
    target = obj
    for k in keys[:-1]:
        target = target.setdefault(k, {})
    target[keys[-1]] = value


def append_to_text(obj: dict, path: str, suffix: str) -> None:
    """Append suffix to obj.path (text). Preserves existing content."""
    keys = path.split(".")
    target = obj
    for k in keys[:-1]:
        target = target.setdefault(k, {})
    current = target.get(keys[-1], "")
    target[keys[-1]] = (current + (" " if current else "") + suffix).strip()


def update_sample(category: str, sample_id: str, set_fields: Dict[str, Any] = None,
                  append_fields: Dict[str, str] = None) -> None:
    """Update one sample identified by id. Adds correction note."""
    path = STAGING / f"{category}.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    found = False
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        obj = json.loads(line)
        if obj.get("id") != sample_id:
            continue
        if set_fields:
            for k, v in set_fields.items():
                set_nested(obj, k, v)
        if append_fields:
            for k, v in append_fields.items():
                append_to_text(obj, k, v)
        # Append correction note
        existing_note = obj.get("notes", "")
        obj["notes"] = (existing_note + CORRECTION_NOTE_SUFFIX).strip()
        lines[i] = json.dumps(obj, ensure_ascii=False)
        found = True
        break
    if not found:
        raise ValueError(f"Sample not found: {category}/{sample_id}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  ✓ {category} / {sample_id}")


# ============================================================
# Apply corrections
# ============================================================

def main():
    print("Applying 15 cross-LLM corrections (2026-05-18)...")
    print()

    # 1. confidentiality_ip_006 -- borderline + low + new reason/suggestion
    # NOTE: violation field already False; only updating other fields per user
    update_sample("confidentiality_ip", "confidentiality_ip_006",
        set_fields={
            "variation_type": "borderline",
            "expected.severity": "low",
            "expected.reason": "保密义务法定无期限限制，约定固定5年期限可能产生歧义：若信息5年后仍未公开，劳动者是否仍负保密义务存争议。实务建议表述为『保密义务持续至该信息为公众所知悉时止』",
            "expected.suggestion": "乙方对本职工作过程中所知悉的甲方商业秘密和技术信息负有保密义务，该义务持续至相关信息为公众所知悉时止",
        })

    # 2. job_change_rights_017 -- borderline + low (变相二次试用期 risk)
    update_sample("job_change_rights", "job_change_rights_017",
        set_fields={
            "variation_type": "borderline",
            "expected.severity": "low",
            "expected.reason": "『试用新岗位3个月』存在被认定为变相二次试用期的风险（劳动合同法第19条同一用人单位与同一劳动者只能约定一次试用期）。虽保留回退机制对劳动者有利，但『试用』措辞可能被穿透审查",
            "expected.suggestion": "调岗后设置不超过3个月的岗位考察期（非试用期），原工资待遇不变。不称职的恢复原岗位",
        })

    # 3. job_change_rights_019 -- type borderline, severity unchanged, append note about closure with 016
    update_sample("job_change_rights", "job_change_rights_019",
        set_fields={"variation_type": "borderline"},
        append_fields={
            "expected.reason": "需警惕与类似016的『合理调岗单方判断权』条款形成闭环。实际执行需能举证：①调岗确属客观情况变化；②经过真实协商过程。",
        })

    # 4. job_change_rights_014 -- severity low → medium (commute distance concern)
    update_sample("job_change_rights", "job_change_rights_014",
        set_fields={"expected.severity": "medium"},
        append_fields={
            "expected.reason": "北京朝阳→大兴距离较远，若未提供交通补贴或通勤时间增加过多，个别法院可能认定为需协商。建议增加通勤补助条款。",
        })

    # 5. job_change_rights_020 -- severity medium → low (project-based norms)
    update_sample("job_change_rights", "job_change_rights_020",
        set_fields={"expected.severity": "low"})

    # 6. non_compete_016 -- fix legal basis (39条第4款 is termination grounds, not prohibition basis)
    update_sample("non_compete", "non_compete_016",
        set_fields={
            "expected.violated_law": ["劳动合同法第3条", "民法典第7条"],
            "expected.reason": "在职期间忠实义务禁止从事与用人单位有竞争关系的兼职，但禁止所有兼职（包括完全不相关的业务）超出了忠实义务的合理范围。劳动者业余时间从事与工作无关且不影响本职的兼职，用人单位无权禁止。忠实义务来源于诚实信用原则（劳动合同法第3条、民法典第7条），而非第39条第4款（该款是解除合同情形）",
            "expected.suggestion": "乙方在职期间不得从事与甲方业务有竞争关系的兼职；其他兼职如不影响本职工作，需提前书面报备",
        })

    # 7. non_compete_020 -- fix违约金 vs 损失 relationship per 民法典 585
    update_sample("non_compete", "non_compete_020",
        set_fields={
            "expected.reason": "违约金与损失赔偿均为违约责任形式，可并存。但实务中法院处理方式为：违约金不足以弥补实际损失的，可主张差额部分（民法典第585条第2款）；违约金过高于损失的，可请求酌减。约定『同时支付』可能被法院视为重复计算",
            "expected.suggestion": "违约金不足以弥补实际损失的，甲方可另行主张差额部分",
        })

    # 8. non_compete_004 -- shorten 司法解释 citation
    # Update violated_law list: replace long form with short form
    path = STAGING / "non_compete.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        obj = json.loads(line)
        if obj.get("id") != "non_compete_004":
            continue
        old_laws = obj["expected"]["violated_law"]
        new_laws = ["劳动争议司法解释（一）第36条" if "最高法关于审理劳动争议" in law else law
                    for law in old_laws]
        obj["expected"]["violated_law"] = new_laws
        obj["notes"] = (obj.get("notes", "") + CORRECTION_NOTE_SUFFIX).strip()
        lines[i] = json.dumps(obj, ensure_ascii=False)
        break
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  ✓ non_compete / non_compete_004")

    # 9. non_compete_009 -- severity low → medium (schema has no low-medium, using medium per user discussion)
    update_sample("non_compete", "non_compete_009",
        set_fields={"expected.severity": "medium"},
        append_fields={
            "expected.reason": "虽合规，但缺少违约金条款将大幅增加用人单位举证难度，实务中建议约定合理违约金。",
        })

    # 10. non_compete_017 -- add note about 实习生 not in 劳动关系
    update_sample("non_compete", "non_compete_017",
        append_fields={
            "expected.reason": "实习生通常不构成劳动关系，竞业限制制度（劳动合同法第23-24条）以劳动关系为前提。且即使参照适用，无经济补偿也违法。",
        })

    # 11. penalty_clause_011 -- borderline (or-clause skip前置程序 risk)
    update_sample("penalty_clause", "penalty_clause_011",
        set_fields={
            "variation_type": "borderline",
            "expected.severity": "low",
            "expected.reason": "业绩不达标可能导致调岗，但『或终止合同』的表述过于绝对。第40条第2款要求先经培训或调岗后仍不能胜任方可解除。如跳过培训/调岗直接终止合同，违反法定前置程序",
            "expected.suggestion": "连续3个月未达标的，公司可调整其工作岗位；调整后仍不能胜任的，公司可提前30日通知或额外支付一个月工资后解除劳动合同，并支付经济补偿",
        })

    # 12. penalty_clause_012 -- fix legal basis (实施条例第26条 → 第90条 + 工资支付规定第16条)
    update_sample("penalty_clause", "penalty_clause_012",
        set_fields={
            "expected.violated_law": ["劳动合同法第90条", "工资支付暂行规定第16条"],
            "expected.severity": "low",
            "expected.reason": "第90条允许因劳动者违法解除造成损失时主张赔偿，但赔偿范围限于直接损失（招聘费、培训费等有票据支持）。『岗位空缺期间预期损失』属间接损失，法院通常不支持，属过度主张",
        })

    # 13. penalty_clause_017 -- severity none → low, note about English training type dispute
    update_sample("penalty_clause", "penalty_clause_017",
        set_fields={"expected.severity": "low"},
        append_fields={
            "expected.reason": "英语培训属于通用技能培训，是否构成第22条『专业技术培训』存争议——部分法院可能不认可普通语言培训可设定服务期。",
        })

    # 14. probation_period_017 -- LEGAL SUBSTANTIVE: violation true → false per 民法典 1259
    # "以上" includes the base number; 3-month contract IS in "3个月以上不满1年" tier
    update_sample("probation_period", "probation_period_017",
        set_fields={
            "expected.violation": False,
            "expected.violated_law": [],
            "expected.severity": "low",
            "expected.reason": "按民法典第1259条，『三个月以上』含本数，3个月整合同属第19条第1款适用范围，试用期上限1个月，约定1个月恰好合规。但实务中因条款表述存在少数争议，建议合同期明确为『3个月零1日』以规避边界风险",
            "expected.suggestion": "当前约定可维持（合规），但建议将合同期设为3个月以上（如3个月零1日）以彻底消除争议",
        })

    # 15. termination_007 -- remove abolished regulation, fix to 第42条第3款
    update_sample("termination", "termination_007",
        set_fields={
            "expected.violated_law": ["劳动合同法第40条第1款", "劳动合同法第42条第3款"],
            "expected.reason": "双重违法：（1）劳动者患病在医疗期内的，不得解除劳动合同（第42条第3款）。『未到医疗期』即解除违法；（2）即使医疗期满后依法解除，也应支付经济补偿。关于医疗补助费，原《违反和解除劳动合同的经济补偿办法》已于2017年废止，现行法律暂无统一强制标准，部分地方法规仍要求支付，建议依地方规定处理",
            "expected.suggestion": "等待医疗期满后再依法处理；解除时支付经济补偿，并根据地方规定协商医疗补助费",
        })

    print()
    print("All 15 corrections applied.")


if __name__ == "__main__":
    main()
