"""Opt-in scientific-use contract test against an external read-only H5AD."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from omicsrepro.verification.config import ScrnaDEContractSpec
from omicsrepro.verification.models import AssuranceLevel, VerificationOutcome
from omicsrepro.verification.scrna_de import verify_scrna_de_preflight

pytestmark = pytest.mark.integration


def _external_path(variable: str) -> Path:
    value = os.environ.get(variable)
    if not value:
        pytest.skip(f"{variable} is not configured")
    return Path(value).resolve()


def test_external_de_preflight_is_read_only_and_fail_closed(tmp_path: Path) -> None:
    data_root = _external_path("OMICSREPRO_DATA_ROOT")
    h5ad = _external_path("OMICSREPRO_H5AD")
    if data_root not in h5ad.parents:
        pytest.fail("OMICSREPRO_H5AD must be inside OMICSREPRO_DATA_ROOT")
    if not h5ad.is_file():
        pytest.fail("OMICSREPRO_H5AD is not a regular file")

    population = os.environ.get("OMICSREPRO_DE_POPULATION")
    condition_column = os.environ.get("OMICSREPRO_DE_CONDITION_COLUMN")
    case = os.environ.get("OMICSREPRO_DE_CASE")
    control = os.environ.get("OMICSREPRO_DE_CONTROL")
    if not all((population, condition_column, case, control)):
        pytest.skip("DE integration contract variables are not fully configured")

    project = tmp_path / "project"
    project.mkdir()
    (project / "omicsrepro.yml").write_text(
        f"""schema_version: 1
project:
  name: external-de-integration
inputs:
  - id: primary
    path: {h5ad}
    format: h5ad
    profile: scrna-basic
""",
        encoding="utf-8",
    )
    before = h5ad.stat()
    receipt = verify_scrna_de_preflight(
        project,
        ScrnaDEContractSpec.model_validate(
            {
                "schema_version": 1,
                "contract": "scrna.de_between_conditions/v0",
                "input_id": "primary",
                "population": {"value": population},
                "condition": {
                    "column": condition_column,
                    "case": case,
                    "control": control,
                },
            }
        ),
    )
    after = h5ad.stat()

    assert receipt.assurance == AssuranceLevel.ARTIFACT_INSPECTION
    assert receipt.verdict in {VerificationOutcome.FAIL, VerificationOutcome.INDETERMINATE}
    assert any(item.code == "ORV190" for item in receipt.checks)
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
