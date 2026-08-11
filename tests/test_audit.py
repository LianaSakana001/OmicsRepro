"""Deterministic end-to-end audit tests."""

from __future__ import annotations

from pathlib import Path

from conftest import write_h5ad

from omicsrepro.audit import audit_project
from omicsrepro.models import Outcome
from omicsrepro.reporting import render_json, render_markdown


def test_valid_project_passes_deterministically(valid_project: Path) -> None:
    first = audit_project(valid_project)
    second = audit_project(valid_project)

    assert first.status == "pass"
    assert first.summary.failed == 0
    assert first.model_dump() == second.model_dump()
    assert render_json(first) == render_json(second)
    assert "H5AD004" in render_markdown(first)


def test_missing_required_column_fails(valid_project: Path) -> None:
    manifest = valid_project / "omicsrepro.yml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            "required_obs_columns: [donor_id]",
            "required_obs_columns: [donor_id, cell_type]",
        ),
        encoding="utf-8",
    )

    report = audit_project(valid_project)
    result = next(item for item in report.checks if item.code == "H5AD005")

    assert report.status == "fail"
    assert result.outcome == Outcome.FAIL
    assert result.evidence["missing"] == ["cell_type"]


def test_shape_mismatch_and_duplicate_index_are_evidence(valid_project: Path) -> None:
    write_h5ad(valid_project / "data" / "input.h5ad", duplicate_obs=True, x_shape=(1, 2))

    report = audit_project(valid_project)
    by_code = {item.code: item for item in report.checks}

    assert by_code["H5AD004"].outcome == Outcome.FAIL
    assert by_code["H5AD004"].evidence["x_shape"] == (1, 2)
    assert by_code["H5AD007"].outcome == Outcome.FAIL
    assert by_code["H5AD007"].evidence["first_duplicate"] == "cell-a"
