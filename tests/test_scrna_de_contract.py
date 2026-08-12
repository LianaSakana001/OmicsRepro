"""Experimental scRNA-seq DE preflight contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import h5py
from conftest import write_h5ad
from typer.testing import CliRunner

from omicsrepro.cli import app
from omicsrepro.verification.config import ScrnaDEContractSpec
from omicsrepro.verification.models import VerificationOutcome
from omicsrepro.verification.scrna_de import verify_scrna_de_preflight

runner = CliRunner()


def _project(tmp_path: Path, rows: list[tuple[str, str, str, str]]) -> Path:
    project = tmp_path / "de-project"
    path = project / "data" / "input.h5ad"
    write_h5ad(path, x_shape=(len(rows), 2), counts_shape=(len(rows), 2), design_rows=rows)
    with h5py.File(path, "r+") as handle:
        counts = handle.require_group("layers").create_dataset(
            "counts", shape=(len(rows), 2), dtype="int32"
        )
        counts[0, 0] = 1
    (project / "omicsrepro.yml").write_text(
        """schema_version: 1
project:
  name: de-fixture
inputs:
  - id: primary
    path: data/input.h5ad
    format: h5ad
    profile: scrna-basic
""",
        encoding="utf-8",
    )
    return project


def _spec() -> ScrnaDEContractSpec:
    return ScrnaDEContractSpec.model_validate(
        {
            "schema_version": 1,
            "contract": "scrna.de_between_conditions/v0",
            "input_id": "primary",
            "population": {"value": "Microglia"},
            "condition": {"column": "disease", "case": "AD", "control": "Control"},
            "replicate": {"concept": "donor", "min_per_group": 2},
        }
    )


def _by_code(receipt: object, code: str) -> object:
    return next(item for item in receipt.checks if item.code == code)  # type: ignore[attr-defined]


def test_preflight_facts_pass_but_execution_remains_indeterminate(tmp_path: Path) -> None:
    project = _project(
        tmp_path,
        [
            ("Microglia", "AD", "D1", "S1"),
            ("Microglia", "AD", "D2", "S2"),
            ("Microglia", "Control", "D3", "S3"),
            ("Microglia", "Control", "D4", "S4"),
        ],
    )

    first = verify_scrna_de_preflight(project, _spec())
    second = verify_scrna_de_preflight(project, _spec())

    assert first.verdict == VerificationOutcome.INDETERMINATE
    assert _by_code(first, "ORV104").outcome == VerificationOutcome.PASS
    assert _by_code(first, "ORV106").outcome == VerificationOutcome.PASS
    assert _by_code(first, "ORV108").evidence["replicates_by_group"] == {
        "AD": 2,
        "Control": 2,
    }
    assert _by_code(first, "ORV190").outcome == VerificationOutcome.INDETERMINATE
    assert first.model_dump() == second.model_dump()


def test_conflicting_donor_condition_mapping_fails_without_leaking_ids(tmp_path: Path) -> None:
    project = _project(
        tmp_path,
        [
            ("Microglia", "AD", "D1", "S1"),
            ("Microglia", "Control", "D1", "S2"),
            ("Microglia", "AD", "D2", "S3"),
            ("Microglia", "Control", "D3", "S4"),
        ],
    )

    receipt = verify_scrna_de_preflight(project, _spec())
    mapping = _by_code(receipt, "ORV107")

    assert receipt.verdict == VerificationOutcome.FAIL
    assert mapping.outcome == VerificationOutcome.FAIL
    assert mapping.evidence["donors_with_multiple_conditions"] == 1
    serialized = json.dumps(receipt.model_dump(mode="json"))
    assert "D1" not in serialized
    assert "S1" not in serialized


def test_safety_limit_abstains_without_scanning_design_values(tmp_path: Path) -> None:
    project = _project(
        tmp_path,
        [
            ("Microglia", "AD", "D1", "S1"),
            ("Microglia", "Control", "D2", "S2"),
        ],
    )
    spec = _spec().model_copy(update={"max_observations": 1})

    receipt = verify_scrna_de_preflight(project, spec)

    assert receipt.verdict == VerificationOutcome.INDETERMINATE
    assert _by_code(receipt, "ORV103").outcome == VerificationOutcome.INDETERMINATE


def test_entity_cardinality_limit_abstains(tmp_path: Path) -> None:
    project = _project(
        tmp_path,
        [
            ("Microglia", "AD", "D1", "S1"),
            ("Microglia", "Control", "D2", "S2"),
        ],
    )
    spec = _spec().model_copy(update={"max_entities": 1})

    receipt = verify_scrna_de_preflight(project, spec)

    assert receipt.verdict == VerificationOutcome.INDETERMINATE
    assert _by_code(receipt, "ORV103").evidence == {
        "reason": "unique donors exceed max_entities"
    }


def test_verify_cli_uses_exit_three_for_unverified_execution(tmp_path: Path) -> None:
    project = _project(
        tmp_path,
        [
            ("Microglia", "AD", "D1", "S1"),
            ("Microglia", "AD", "D2", "S2"),
            ("Microglia", "Control", "D3", "S3"),
            ("Microglia", "Control", "D4", "S4"),
        ],
    )
    contract = tmp_path / "contract.yml"
    contract.write_text(
        """schema_version: 1
contract: scrna.de_between_conditions/v0
input_id: primary
population:
  value: Microglia
condition:
  column: disease
  case: AD
  control: Control
replicate:
  concept: donor
  min_per_group: 2
""",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["verify", str(project), "--contract-file", str(contract)],
    )

    assert result.exit_code == 3
    assert json.loads(result.stdout)["verdict"] == "indeterminate"
