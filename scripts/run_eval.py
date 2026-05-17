#!/usr/bin/env python3
"""CLI to run eval over labeled data with various baseline detectors.

Examples:
    python scripts/run_eval.py                          # all categories, all baselines
    python scripts/run_eval.py --detector violation     # single detector
    python scripts/run_eval.py --category probation_period
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make src/ importable
SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from eval.harness import (  # noqa: E402
    ALL_CATEGORIES,
    DETECTORS,
    run_all_eval,
    run_category_eval,
    format_metrics_table,
)


def main():
    parser = argparse.ArgumentParser(description="Run agent eval against labeled JSONL.")
    parser.add_argument(
        "--detector",
        choices=list(DETECTORS.keys()) + ["all"],
        default="all",
        help="Which baseline detector to use (or 'all' for comparison)",
    )
    parser.add_argument(
        "--category",
        choices=ALL_CATEGORIES + ["all"],
        default="all",
        help="Which taxonomy category to eval",
    )
    args = parser.parse_args()

    detectors_to_run = [args.detector] if args.detector != "all" else list(DETECTORS.keys())

    for det_name in detectors_to_run:
        detector = DETECTORS[det_name]
        print()
        print("=" * 90)
        print(f"DETECTOR: {det_name}")
        print("=" * 90)
        if args.category == "all":
            results = run_all_eval(detector)
        else:
            results = [run_category_eval(args.category, detector)]
        print(format_metrics_table(results))


if __name__ == "__main__":
    main()
