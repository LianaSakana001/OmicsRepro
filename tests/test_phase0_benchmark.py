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
        "p0-dev-009",
        "p0-dev-010",
        "p0-dev-011",
        "p0-dev-012",
        "p0-dev-013",
        "p0-dev-014",
        "p0-dev-015",
        "p0-dev-016",
    ]
    assert report["case_count"] == 16
    assert report["matched"] == 16
    assert report["actual_l1_decisions"] == {
        "fail": 10,
        "indeterminate": 2,
        "pass": 4,
    }
    assert report["label_review"] == {"pending": 16}
    assert report["review_round"] == "phase0-development-r1"
    assert report["baseline_protocol"] == {
        "id": "phase0-scrna-de-baselines/v1",
        "baseline_count": 5,
        "network_access": "disabled",
    }
