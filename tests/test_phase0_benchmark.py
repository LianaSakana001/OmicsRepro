"""Tests for the publishable Phase 0 development corpus."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "benchmarks" / "phase0" / "run_development.py"


def test_development_harness_matches_expected_l1_outcomes() -> None:
    completed = subprocess.run(
        [sys.executable, str(RUNNER)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    assert [case["id"] for case in report["cases"]] == [
        "p0-dev-001",
        "p0-dev-002",
        "p0-dev-003",
        "p0-dev-004",
        "p0-dev-005",
        "p0-dev-006",
        "p0-dev-007",
        "p0-dev-008",
    ]
    assert report["case_count"] == 8
    assert report["matched"] == 8
    assert report["actual_l1_decisions"] == {
        "fail": 5,
        "indeterminate": 1,
        "pass": 2,
    }
    assert report["label_review"] == {"pending": 8}
