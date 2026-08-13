"""Experimental preflight for ``scrna.de_between_conditions/v0``."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import h5py

from omicsrepro import __version__
from omicsrepro.audit import audit_project
from omicsrepro.config import discover_manifest, load_manifest
from omicsrepro.models import Outcome
from omicsrepro.verification.config import ScrnaDEContractSpec
from omicsrepro.verification.h5ad_facts import (
    UnsupportedColumnEncoding,
    column_length,
    iter_column,
)
from omicsrepro.verification.models import (
    AssuranceLevel,
    VerificationCheck,
    VerificationOutcome,
    VerificationReceipt,
)

CONTRACT_ID = "scrna.de_between_conditions/v0"


class EvidenceLimitExceeded(ValueError):
    """Raised when aggregate design evidence exceeds an explicit memory bound."""


def _resolved(root: Path, configured: str) -> Path:
    path = Path(configured).expanduser()
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _finding(
    code: str,
    outcome: VerificationOutcome,
    message: str,
    *,
    evidence: dict[str, object] | None = None,
    remediation: str | None = None,
) -> VerificationCheck:
    return VerificationCheck(
        code=code,
        outcome=outcome,
        message=message,
        evidence=evidence or {},
        remediation=remediation,
    )


def _early_receipt(
    *, project: str, spec: ScrnaDEContractSpec, check: VerificationCheck
) -> VerificationReceipt:
    return VerificationReceipt.build(
        tool_version=__version__,
        contract=CONTRACT_ID,
        contract_status="experimental",
        project=project,
        subject=_subject(spec),
        assurance=AssuranceLevel.ARTIFACT_INSPECTION,
        checks=[check],
        limitations=["No analysis code is executed by this experimental contract."],
    )


def _subject(spec: ScrnaDEContractSpec) -> dict[str, str]:
    return {
        "input_id": spec.input_id,
        "population": spec.population.value,
        "comparison": f"{spec.condition.case} vs {spec.condition.control}",
        "biological_replicate": spec.replicate.concept,
    }


def verify_scrna_de_preflight(project: Path, spec: ScrnaDEContractSpec) -> VerificationReceipt:
    """Evaluate only artifact-level preconditions and abstain on execution claims."""

    manifest_path = discover_manifest(project)
    manifest = load_manifest(manifest_path)
    root = manifest_path.parent
    inputs = {item.id: item for item in manifest.inputs}
    item = inputs.get(spec.input_id)
    if item is None:
        return _early_receipt(
            project=manifest.project.name,
            spec=spec,
            check=_finding(
                "ORV001",
                VerificationOutcome.FAIL,
                "contract input_id is not declared by the project manifest",
                evidence={"input_id": spec.input_id},
                remediation="Select an input ID declared in omicsrepro.yml.",
            ),
        )

    report = audit_project(project)
    dataset = next((value for value in report.datasets if value.input_id == spec.input_id), None)
    configured_target = item.path
    structural_failures = [
        result.code
        for result in report.checks
        if result.target == configured_target
        and result.outcome == Outcome.FAIL
        and result.code in {"ORP101", "H5AD001", "H5AD002", "H5AD003", "H5AD004"}
    ]
    if dataset is None or structural_failures:
        return _early_receipt(
            project=manifest.project.name,
            spec=spec,
            check=_finding(
                "ORV101",
                VerificationOutcome.FAIL,
                "input is not structurally inspectable as the declared H5AD artifact",
                evidence={"failed_rules": structural_failures},
                remediation="Repair the H5AD structure before scientific-use verification.",
            ),
        )

    donor_column = dataset.semantic_columns.get("donor")
    sample_column = dataset.semantic_columns.get("sample")
    population_column = spec.population.column or dataset.semantic_columns.get("cell_type")
    required_columns = {
        "population": population_column,
        "condition": spec.condition.column,
        "donor": donor_column,
        "sample": sample_column,
    }
    missing_concepts = sorted(name for name, column in required_columns.items() if column is None)
    checks: list[VerificationCheck] = []
    if missing_concepts:
        checks.append(
            _finding(
                "ORV102",
                VerificationOutcome.FAIL,
                "required scientific-use metadata concepts are unresolved",
                evidence={"missing_concepts": missing_concepts},
                remediation=(
                    "Use scrna-basic or scrna-publication and declare semantic aliases; "
                    "set an explicit population column when needed."
                ),
            )
        )
        return VerificationReceipt.build(
            tool_version=__version__,
            contract=CONTRACT_ID,
            contract_status="experimental",
            project=manifest.project.name,
            subject=_subject(spec),
            assurance=AssuranceLevel.ARTIFACT_INSPECTION,
            checks=checks,
            limitations=["No analysis code is executed by this experimental contract."],
        )

    path = _resolved(root, item.path)
    assert all(required_columns.values())
    with h5py.File(path, "r") as handle:
        obs = handle.get("obs")
        assert isinstance(obs, h5py.Group)
        absent_columns = sorted(
            name
            for name, column in required_columns.items()
            if column not in obs
        )
        if absent_columns:
            checks.append(
                _finding(
                    "ORV102",
                    VerificationOutcome.FAIL,
                    "resolved scientific-use metadata columns are absent from obs",
                    evidence={"missing_concepts": absent_columns},
                    remediation="Correct the contract column or semantic alias declaration.",
                )
            )
        else:
            nodes = {name: obs[str(column)] for name, column in required_columns.items()}
            try:
                lengths = {name: column_length(node) for name, node in nodes.items()}
                if len(set(lengths.values())) != 1:
                    checks.append(
                        _finding(
                            "ORV103",
                            VerificationOutcome.FAIL,
                            "scientific-use metadata columns have inconsistent lengths",
                            evidence={"column_lengths": lengths},
                            remediation="Re-export aligned obs metadata.",
                        )
                    )
                elif next(iter(lengths.values())) > spec.max_observations:
                    checks.append(
                        _finding(
                            "ORV103",
                            VerificationOutcome.INDETERMINATE,
                            "metadata scan exceeds the contract safety limit",
                            evidence={
                                "observations": next(iter(lengths.values())),
                                "max_observations": spec.max_observations,
                            },
                            remediation=(
                                "Raise max_observations explicitly after reviewing resource limits."
                            ),
                        )
                    )
                else:
                    checks.extend(_mapping_checks(nodes, spec))
            except (EvidenceLimitExceeded, UnsupportedColumnEncoding) as exc:
                checks.append(
                    _finding(
                        "ORV103",
                        VerificationOutcome.INDETERMINATE,
                        "v0 cannot inspect one or more metadata column encodings",
                        evidence={"reason": str(exc)},
                        remediation="Re-export plain or AnnData categorical obs columns.",
                    )
                )

    raw_counts = next(
        (
            result
            for result in report.checks
            if result.target == configured_target and result.code == "H5AD103"
        ),
        None,
    )
    if raw_counts is None:
        checks.append(
            _finding(
                "ORV106",
                VerificationOutcome.INDETERMINATE,
                "count-compatible matrix evidence was not produced",
                remediation="Apply scrna-basic/publication so raw-count evidence is inspected.",
            )
        )
    else:
        checks.append(
            _finding(
                "ORV106",
                (
                    VerificationOutcome.PASS
                    if raw_counts.outcome == Outcome.PASS
                    else VerificationOutcome.FAIL
                ),
                raw_counts.message,
                evidence={
                    "location": raw_counts.evidence.get("location"),
                    "shape": raw_counts.evidence.get("shape"),
                },
                remediation=raw_counts.remediation,
            )
        )

    checks.append(
        _finding(
            "ORV190",
            VerificationOutcome.INDETERMINATE,
            "actual aggregation, design, contrast, method, and result binding were not verified",
            evidence={"assurance": AssuranceLevel.ARTIFACT_INSPECTION.value},
            remediation=(
                "A future evidence adapter or instrumented run is required for postflight claims."
            ),
        )
    )
    return VerificationReceipt.build(
        tool_version=__version__,
        contract=CONTRACT_ID,
        contract_status="experimental",
        project=manifest.project.name,
        subject=_subject(spec),
        assurance=AssuranceLevel.ARTIFACT_INSPECTION,
        checks=checks,
        limitations=[
            "This v0 contract verifies artifact-level preconditions only.",
            "It does not certify biological truth, method optimality, or the executed analysis.",
            "No analysis code is executed and no source artifact is modified.",
        ],
    )


def _mapping_checks(
    nodes: dict[str, h5py.Dataset | h5py.Group], spec: ScrnaDEContractSpec
) -> list[VerificationCheck]:
    donors_by_condition: dict[str, set[str]] = defaultdict(set)
    donor_conditions: dict[str, set[str]] = defaultdict(set)
    sample_donors: dict[str, set[str]] = defaultdict(set)
    target_cells = 0
    missing_donor = 0
    missing_sample = 0
    missing_condition = 0
    other_condition_cells = 0
    concepts = ("population", "condition", "donor", "sample")
    rows = zip(
        *(iter_column(nodes[name], max_categories=spec.max_categories) for name in concepts),
        strict=True,
    )
    for population, condition, donor, sample in rows:
        if population != spec.population.value:
            continue
        target_cells += 1
        missing_donor += donor is None
        missing_sample += sample is None
        missing_condition += condition is None
        if condition is not None and condition not in {
            spec.condition.case,
            spec.condition.control,
        }:
            other_condition_cells += 1
        if donor is not None and condition is not None:
            donor_conditions[donor].add(condition)
            if len(donor_conditions) > spec.max_entities:
                raise EvidenceLimitExceeded("unique donors exceed max_entities")
            if condition in {spec.condition.case, spec.condition.control}:
                donors_by_condition[condition].add(donor)
        if sample is not None and donor is not None:
            sample_donors[sample].add(donor)
            if len(sample_donors) > spec.max_entities:
                raise EvidenceLimitExceeded("unique samples exceed max_entities")

    checks: list[VerificationCheck] = []
    checks.append(
        _finding(
            "ORV104",
            VerificationOutcome.PASS if target_cells else VerificationOutcome.FAIL,
            "declared population is present" if target_cells else "declared population is absent",
            evidence={"selected_observations": target_cells},
            remediation=None if target_cells else "Correct the population label or input artifact.",
        )
    )
    missing = {
        "donor": missing_donor,
        "sample": missing_sample,
        "condition": missing_condition,
    }
    checks.append(
        _finding(
            "ORV105",
            VerificationOutcome.PASS if not any(missing.values()) else VerificationOutcome.FAIL,
            (
                "selected observations have complete design metadata"
                if not any(missing.values())
                else "selected observations contain missing design metadata"
            ),
            evidence={"selected_observations": target_cells, "missing_counts": missing},
            remediation=(
                None
                if not any(missing.values())
                else "Resolve or explicitly exclude observations with missing design metadata."
            ),
        )
    )
    donor_conflicts = sum(len(values) > 1 for values in donor_conditions.values())
    sample_conflicts = sum(len(values) > 1 for values in sample_donors.values())
    checks.append(
        _finding(
            "ORV107",
            (
                VerificationOutcome.PASS
                if donor_conflicts == 0 and sample_conflicts == 0
                else VerificationOutcome.FAIL
            ),
            (
                "sample-to-donor and donor-to-condition mappings are single-valued"
                if donor_conflicts == 0 and sample_conflicts == 0
                else "design metadata contains conflicting biological mappings"
            ),
            evidence={
                "donors_with_multiple_conditions": donor_conflicts,
                "samples_with_multiple_donors": sample_conflicts,
            },
            remediation=(
                None
                if donor_conflicts == 0 and sample_conflicts == 0
                else "Correct conflicting mappings before differential expression."
            ),
        )
    )
    replicate_counts = {
        spec.condition.case: len(donors_by_condition[spec.condition.case]),
        spec.condition.control: len(donors_by_condition[spec.condition.control]),
    }
    enough_replicates = all(
        count >= spec.replicate.min_per_group for count in replicate_counts.values()
    )
    checks.append(
        _finding(
            "ORV108",
            VerificationOutcome.PASS if enough_replicates else VerificationOutcome.FAIL,
            (
                "declared groups meet the biological replicate floor"
                if enough_replicates
                else "one or more declared groups lack the required biological replicates"
            ),
            evidence={
                "replicates_by_group": replicate_counts,
                "minimum_per_group": spec.replicate.min_per_group,
            },
            remediation=(
                None
                if enough_replicates
                else "Revise the design or minimum only with scientific justification."
            ),
        )
    )
    if other_condition_cells:
        checks.append(
            _finding(
                "ORV109",
                VerificationOutcome.WARN,
                "selected population also contains observations outside the declared contrast",
                evidence={"other_condition_observations": other_condition_cells},
                remediation="Confirm that downstream analysis subsets exactly the declared groups.",
            )
        )
    return checks
