"""Eval harness for labor contract review agent.

Loads eval JSONL data + runs detector + computes per-category P/R/F1.

Usage:
    from eval.harness import run_eval, load_eval_set, stub_detector
    metrics = run_eval("probation_period", stub_detector)

Or via CLI:
    python scripts/run_eval.py
    python scripts/run_eval.py --category probation_period
    python scripts/run_eval.py --detector stub|always_violation|none

Design notes:
- Detector is any callable (str) -> Prediction. Decouples eval from detection logic.
- Initial detectors are dumb baselines (always-true, always-false) to verify harness works.
- P2 will plug in real LLM/RAG detectors via the same interface.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable, Dict, List, Optional


# ====================================================================
# Data types
# ====================================================================

@dataclass
class EvalSample:
    """One labeled eval example from JSONL."""
    id: str
    clause: str
    context: str
    expected_violation: bool
    expected_category: str
    expected_severity: str
    variation_type: str
    raw: dict  # full original JSON for debugging


@dataclass
class Prediction:
    """Detector output."""
    violation: bool
    category: Optional[str] = None
    severity: Optional[str] = None  # high/medium/low/none
    confidence: float = 1.0
    reason: str = ""
    violated_law: List[str] = field(default_factory=list)


@dataclass
class CategoryMetrics:
    """Per-category eval result."""
    category: str
    total: int
    tp: int
    fp: int
    fn: int
    tn: int
    precision: float
    recall: float
    f1: float
    accuracy: float
    # 严重程度匹配（次要指标）
    severity_match_rate: float = 0.0
    # 按 variation_type 的细分
    by_variation: Dict[str, Dict[str, int]] = field(default_factory=dict)


# ====================================================================
# Loaders
# ====================================================================

def project_root() -> Path:
    """Find project root (the dir containing data/, eval/, src/)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "eval" / "labeled").exists():
            return parent
    raise RuntimeError("Cannot find project root with eval/labeled/")


def load_eval_set(category: str, base_dir: Optional[Path] = None) -> List[EvalSample]:
    """Load JSONL eval samples for a category."""
    base = base_dir if base_dir else (project_root() / "eval" / "labeled")
    path = base / f"{category}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"Eval file not found: {path}")
    samples = []
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{line_no} invalid JSON: {e}")
            exp = obj.get("expected", {})
            samples.append(EvalSample(
                id=obj["id"],
                clause=obj["clause"],
                context=obj.get("context", ""),
                expected_violation=exp.get("violation", False),
                expected_category=exp.get("category", category),
                expected_severity=exp.get("severity", "none"),
                variation_type=obj.get("variation_type", "?"),
                raw=obj,
            ))
    return samples


# ====================================================================
# Metrics
# ====================================================================

def compute_metrics(
    samples: List[EvalSample],
    predictions: List[Prediction],
    category: str,
) -> CategoryMetrics:
    """Compute per-category P/R/F1 + breakdowns."""
    if len(samples) != len(predictions):
        raise ValueError(f"Mismatch: {len(samples)} samples vs {len(predictions)} predictions")

    tp = fp = fn = tn = 0
    sev_match = 0
    by_var: Dict[str, Dict[str, int]] = {}

    for s, p in zip(samples, predictions):
        # Binary violation detection
        if s.expected_violation and p.violation:
            tp += 1
            outcome = "tp"
        elif s.expected_violation and not p.violation:
            fn += 1
            outcome = "fn"
        elif not s.expected_violation and p.violation:
            fp += 1
            outcome = "fp"
        else:
            tn += 1
            outcome = "tn"

        # Severity match (secondary)
        if (p.severity or "none") == s.expected_severity:
            sev_match += 1

        # Track by variation_type
        v = s.variation_type
        if v not in by_var:
            by_var[v] = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
        by_var[v][outcome] += 1

    total = len(samples)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / total if total > 0 else 0.0

    return CategoryMetrics(
        category=category,
        total=total,
        tp=tp, fp=fp, fn=fn, tn=tn,
        precision=precision,
        recall=recall,
        f1=f1,
        accuracy=accuracy,
        severity_match_rate=sev_match / total if total > 0 else 0.0,
        by_variation=by_var,
    )


# ====================================================================
# Runner
# ====================================================================

DetectorFn = Callable[[str], Prediction]


def run_category_eval(category: str, detector: DetectorFn) -> CategoryMetrics:
    """Run eval for one category."""
    samples = load_eval_set(category)
    predictions = [detector(s.clause) for s in samples]
    return compute_metrics(samples, predictions, category)


ALL_CATEGORIES = [
    "probation_period",
    "penalty_clause",
    "service_period",
    "working_hours",
    "social_insurance",
    "job_change_rights",
    "non_compete",
    "confidentiality_ip",
    "termination",
    "wage_composition",
]


def run_all_eval(detector: DetectorFn) -> List[CategoryMetrics]:
    """Run eval for all categories."""
    return [run_category_eval(cat, detector) for cat in ALL_CATEGORIES]


# ====================================================================
# Baseline detectors (stubs for harness verification)
# ====================================================================

def stub_compliant_detector(clause: str) -> Prediction:
    """Always predict 合规。Worst case for violation_clear samples."""
    return Prediction(violation=False, severity="none", confidence=0.0,
                     reason="stub: always compliant")


def stub_violation_detector(clause: str) -> Prediction:
    """Always predict 违法。Worst case for compliant samples."""
    return Prediction(violation=True, severity="high", confidence=0.0,
                     reason="stub: always violation")


def stub_random_detector(clause: str) -> Prediction:
    """50/50 random predictions. Baseline."""
    import random
    v = random.random() > 0.5
    return Prediction(violation=v, severity="medium" if v else "none",
                     confidence=0.5, reason="stub: random")


DETECTORS = {
    "compliant": stub_compliant_detector,
    "violation": stub_violation_detector,
    "random": stub_random_detector,
}


# ====================================================================
# Pretty print
# ====================================================================

def format_metrics_table(results: List[CategoryMetrics]) -> str:
    """Pretty-print results as a table."""
    lines = []
    lines.append(f"{'Category':<22} {'N':>4} {'P':>6} {'R':>6} {'F1':>6} {'Acc':>6} {'SevMatch':>9}  {'TP/FP/FN/TN'}")
    lines.append("-" * 90)
    for m in results:
        lines.append(
            f"{m.category:<22} {m.total:>4} "
            f"{m.precision:.3f} {m.recall:.3f} {m.f1:.3f} "
            f"{m.accuracy:.3f} {m.severity_match_rate:.3f}     "
            f"{m.tp:>3}/{m.fp:>3}/{m.fn:>3}/{m.tn:>3}"
        )
    # 总计 (micro average)
    total_tp = sum(m.tp for m in results)
    total_fp = sum(m.fp for m in results)
    total_fn = sum(m.fn for m in results)
    total_tn = sum(m.tn for m in results)
    total_n = sum(m.total for m in results)
    micro_p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    micro_r = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) > 0 else 0.0
    micro_acc = (total_tp + total_tn) / total_n if total_n > 0 else 0.0
    lines.append("-" * 90)
    lines.append(
        f"{'MICRO AVG':<22} {total_n:>4} "
        f"{micro_p:.3f} {micro_r:.3f} {micro_f1:.3f} "
        f"{micro_acc:.3f}     -      "
        f"{total_tp:>3}/{total_fp:>3}/{total_fn:>3}/{total_tn:>3}"
    )
    return "\n".join(lines)
