"""Tests for the publishable Phase 0 development corpus."""

from __future__ import annotations

from benchmarks.phase0.run_development import load_cases, run_development


def test_development_cases_have_unique_frozen_order() -> None:
    cases = load_cases()

    assert [case.id for case in cases] == [
        "p0-dev-001",
        "p0-dev-002",
        "p0-dev-003",
        "p0-dev-004",
        "p0-dev-005",
        "p0-dev-006",
        "p0-dev-007",
        "p0-dev-008",
    ]
    assert all(case.provenance.kind == "synthetic" for case in cases)
    assert all(case.partition == "development" for case in cases)


def test_development_harness_matches_expected_l1_outcomes() -> None:
    report = run_development()

    assert report["case_count"] == 8
    assert report["matched"] == 8
    assert report["actual_l1_decisions"] == {
        "fail": 5,
        "indeterminate": 1,
        "pass": 2,
    }
    assert report["label_review"] == {"pending": 8}
