"""Build and score the public Phase 0 development cases deterministically."""

from __future__ import annotations

import json
import tempfile
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Literal

import h5py
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from omicsrepro.verification.config import ScrnaDEContractSpec
from omicsrepro.verification.models import (
    VerificationCheck,
    VerificationOutcome,
    VerificationReceipt,
)
from omicsrepro.verification.scrna_de import verify_scrna_de_preflight

CASE_ROOT = Path(__file__).parent / "development" / "cases"
REVIEW_SHEET = Path(__file__).parent / "review" / "label-review.yml"
BASELINE_PROTOCOL = Path(__file__).parent / "baselines" / "protocol.yml"
EXCLUDED_L1_CODES = frozenset({"ORV190"})

CaseDecision = Literal["pass", "fail", "indeterminate"]
CaseClass = Literal["pass", "fail", "near_miss", "ambiguous", "decoy", "corrupted", "stale"]


class Provenance(BaseModel):
    """Redistribution and origin declaration for one development fixture."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["synthetic"]
    generator: str = Field(min_length=1)
    license: str = Field(min_length=1)


class CountsFixture(BaseModel):
    """Count-matrix mutation used to derive a tiny H5AD fixture."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: Literal["valid", "absent", "non_integer", "shape_mismatch"]


class Fixture(BaseModel):
    """Synthetic design rows and matrix behavior for one case."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    design_rows: list[tuple[str, str, str, str]] = Field(min_length=1, max_length=1_000)
    counts: CountsFixture


class ExpectedResult(BaseModel):
    """Reviewed expectations for the public development case."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    l1_decision: CaseDecision
    rule_outcomes: dict[str, VerificationOutcome] = Field(min_length=1)
    allowed_l1_decisions: list[CaseDecision]


class LabelReview(BaseModel):
    """Independent label-review state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["pending", "reviewed"]
    reviewer: str | None = None

    @model_validator(mode="after")
    def reviewer_matches_status(self) -> LabelReview:
        """Require a reviewer only after a label is independently reviewed."""

        if self.status == "reviewed" and not self.reviewer:
            raise ValueError("reviewed labels require a reviewer")
        if self.status == "pending" and self.reviewer is not None:
            raise ValueError("pending labels cannot name a reviewer")
        return self


class DevelopmentCase(BaseModel):
    """Strict schema for one publishable Phase 0 development case."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1]
    id: str = Field(pattern=r"^p0-dev-[0-9]{3}$")
    partition: Literal["development"]
    class_: CaseClass = Field(alias="class")
    failure_family: str = Field(pattern=r"^[a-z0-9_]+$")
    severity: Literal["control", "low", "medium", "high"]
    title: str = Field(min_length=3)
    rationale: str = Field(min_length=20)
    case_author: str = Field(min_length=1)
    provenance: Provenance
    fixture: Fixture
    contract: ScrnaDEContractSpec
    expected: ExpectedResult
    privacy_canaries: list[str] = Field(min_length=1)
    label_review: LabelReview

    @model_validator(mode="after")
    def case_is_consistent(self) -> DevelopmentCase:
        """Reject labels that would blur the public development-set boundary."""

        if self.class_ == "ambiguous" and not self.expected.allowed_l1_decisions:
            raise ValueError("ambiguous cases require allowed_l1_decisions")
        if self.class_ != "ambiguous" and self.expected.allowed_l1_decisions:
            raise ValueError("only ambiguous cases may declare allowed_l1_decisions")
        if len(self.privacy_canaries) != len(set(self.privacy_canaries)):
            raise ValueError("privacy_canaries must be unique")
        if any(not value.strip() for value in self.privacy_canaries):
            raise ValueError("privacy_canaries cannot contain empty values")
        return self


class ReviewEntry(BaseModel):
    """Independent scientific and privacy review for one proposed case label."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str = Field(pattern=r"^p0-dev-[0-9]{3}$")
    status: Literal["pending", "approved"]
    proposed_l1_decision: CaseDecision
    proposed_severity: Literal["control", "low", "medium", "high"]
    scientific_rationale_review: Literal["pending", "approved"]
    rule_outcomes_review: Literal["pending", "approved"]
    privacy_review: Literal["pending", "approved"]
    reviewer: str | None = None
    reviewed_at: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def approval_is_complete(self) -> ReviewEntry:
        """Prevent partial review state from being presented as approval."""

        reviews = {
            self.scientific_rationale_review,
            self.rule_outcomes_review,
            self.privacy_review,
        }
        if self.status == "approved":
            if reviews != {"approved"} or not self.reviewer or not self.reviewed_at:
                raise ValueError("approved labels require all reviews, reviewer, and date")
            try:
                date.fromisoformat(self.reviewed_at)
            except ValueError as exc:
                raise ValueError("reviewed_at must use ISO YYYY-MM-DD format") from exc
        elif reviews != {"pending"} or self.reviewer is not None or self.reviewed_at is not None:
            raise ValueError("pending labels cannot contain completed review fields")
        return self


class ReviewSheet(BaseModel):
    """Versioned review packet kept separate from case implementation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1]
    round: str = Field(min_length=1)
    independence_rule: str = Field(min_length=20)
    cases: list[ReviewEntry] = Field(min_length=1)


class BaselineSpec(BaseModel):
    """One comparator with a fixed evidence budget and repetition count."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: Literal[
        "agent",
        "agent_expert_instructions",
        "native_validators",
        "omicsrepro",
        "agent_omicsrepro",
    ]
    kind: Literal["deterministic", "stochastic"]
    repetitions: int = Field(ge=1, le=20)
    instructions: str | None
    receives_omicsrepro_receipt: bool
    score_only_documented_scope: bool


class BaselineProtocol(BaseModel):
    """Machine-checked common protocol for the five Phase 0 comparators."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1]
    id: str = Field(min_length=1)
    contract: Literal["scrna.de_between_conditions/v0"]
    network_access: Literal["disabled"]
    evidence_budget: list[str] = Field(min_length=1)
    output_fields: list[str] = Field(min_length=1)
    output_schema: str = Field(min_length=1)
    baselines: list[BaselineSpec] = Field(min_length=5, max_length=5)

    @model_validator(mode="after")
    def exactly_five_comparators(self) -> BaselineProtocol:
        """Keep the approved comparison set complete and non-duplicated."""

        expected = {
            "agent",
            "agent_expert_instructions",
            "native_validators",
            "omicsrepro",
            "agent_omicsrepro",
        }
        actual = {item.id for item in self.baselines}
        if actual != expected or len(self.baselines) != len(actual):
            raise ValueError("baseline protocol must contain each approved comparator exactly once")
        receipt_consumers = {
            item.id for item in self.baselines if item.receives_omicsrepro_receipt
        }
        if receipt_consumers != {"agent_omicsrepro"}:
            raise ValueError("only agent_omicsrepro may receive an OmicsRepro receipt")
        return self


class CaseResult(BaseModel):
    """Compact, non-identifying result for one development case."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    expected: CaseDecision
    actual: CaseDecision
    matched: bool
    label_review: Literal["pending", "reviewed"]


def load_cases(root: Path = CASE_ROOT) -> list[DevelopmentCase]:
    """Load a unique, ordered set of strict development case definitions."""

    paths = sorted(root.glob("*.yml"))
    if not paths:
        raise ValueError(f"no Phase 0 development cases found under {root}")
    cases = [
        DevelopmentCase.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
        for path in paths
    ]
    ids = [case.id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Phase 0 development case IDs must be unique")
    return sorted(cases, key=lambda case: case.id)


def load_review_sheet(
    cases: list[DevelopmentCase], path: Path = REVIEW_SHEET
) -> ReviewSheet:
    """Load the independent review packet and prove it matches case metadata."""

    sheet = ReviewSheet.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    by_id = {case.id: case for case in cases}
    entries = {entry.case_id: entry for entry in sheet.cases}
    if len(entries) != len(sheet.cases) or set(entries) != set(by_id):
        raise ValueError("label review sheet must contain every development case exactly once")
    for case_id, case in by_id.items():
        entry = entries[case_id]
        if entry.proposed_l1_decision != case.expected.l1_decision:
            raise ValueError(f"{case_id}: review-sheet decision differs from the case")
        if entry.proposed_severity != case.severity:
            raise ValueError(f"{case_id}: review-sheet severity differs from the case")
        expected_status = "approved" if case.label_review.status == "reviewed" else "pending"
        if entry.status != expected_status:
            raise ValueError(f"{case_id}: review status differs from the case")
        if entry.status == "approved":
            if entry.reviewer == case.case_author:
                raise ValueError(f"{case_id}: label reviewer must be independent of case author")
            if entry.reviewer != case.label_review.reviewer:
                raise ValueError(f"{case_id}: reviewer differs between review sheet and case")
    return sheet


def load_baseline_protocol(path: Path = BASELINE_PROTOCOL) -> BaselineProtocol:
    """Load the fixed five-way comparison protocol and instruction references."""

    protocol = BaselineProtocol.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    root = path.parent.resolve()
    output_schema = (root / protocol.output_schema).resolve()
    if root not in output_schema.parents or not output_schema.is_file():
        raise ValueError("baseline output schema is missing or outside baseline root")
    schema = json.loads(output_schema.read_text(encoding="utf-8"))
    if set(protocol.output_fields) != set(schema.get("required", [])):
        raise ValueError("baseline protocol fields differ from the output schema")
    for baseline in protocol.baselines:
        if baseline.instructions is None:
            continue
        instruction_path = (root / baseline.instructions).resolve()
        if root not in instruction_path.parents or not instruction_path.is_file():
            raise ValueError(f"{baseline.id}: instruction file is missing or outside baseline root")
    return protocol


def l1_artifact_decision(receipt: VerificationReceipt) -> CaseDecision:
    """Project a receipt onto L1 checks without weakening the public verdict."""

    checks = [check for check in receipt.checks if check.code not in EXCLUDED_L1_CODES]
    if not checks:
        return "indeterminate"
    if any(check.outcome == VerificationOutcome.FAIL for check in checks):
        return "fail"
    if any(check.outcome == VerificationOutcome.INDETERMINATE for check in checks):
        return "indeterminate"
    return "pass"


def _write_fixture(project: Path, case: DevelopmentCase) -> None:
    """Derive a tiny H5AD project without persisting biological data in Git."""

    rows = case.fixture.design_rows
    path = project / "data" / "input.h5ad"
    path.parent.mkdir(parents=True)
    string = h5py.string_dtype(encoding="utf-8")
    with h5py.File(path, "w") as handle:
        handle.attrs["encoding-type"] = "anndata"
        handle.attrs["encoding-version"] = "0.1.0"
        obs = handle.create_group("obs")
        obs.attrs["_index"] = "_index"
        obs.create_dataset(
            "_index", data=[f"synthetic-cell-{index}" for index in range(len(rows))], dtype=string
        )
        obs.create_dataset("cell_type", data=[row[0] for row in rows], dtype=string)
        obs.create_dataset("disease", data=[row[1] for row in rows], dtype=string)
        obs.create_dataset("donor_id", data=[row[2] for row in rows], dtype=string)
        obs.create_dataset("sample_id", data=[row[3] for row in rows], dtype=string)
        var = handle.create_group("var")
        var.attrs["_index"] = "_index"
        var.create_dataset("_index", data=["SYN-GENE1", "SYN-GENE2"], dtype=string)
        var.create_dataset("gene_ids", data=["SYN-G1", "SYN-G2"], dtype=string)
        handle.create_dataset("X", shape=(len(rows), 2), dtype="float32")
        if case.fixture.counts.mode != "absent":
            layers = handle.create_group("layers")
            if case.fixture.counts.mode == "valid":
                counts = layers.create_dataset("counts", shape=(len(rows), 2), dtype="int32")
                counts[0, 0] = 1
            elif case.fixture.counts.mode == "non_integer":
                counts = layers.create_dataset("counts", shape=(len(rows), 2), dtype="float32")
                counts[0, 0] = 0.5
            else:
                counts = layers.create_dataset(
                    "counts", shape=(max(1, len(rows) - 1), 2), dtype="int32"
                )
                counts[0, 0] = 1

    (project / "omicsrepro.yml").write_text(
        f"""schema_version: 1
project:
  name: {case.id}
inputs:
  - id: primary
    path: data/input.h5ad
    format: h5ad
    profile: scrna-basic
""",
        encoding="utf-8",
    )


def _checks_by_code(checks: list[VerificationCheck]) -> dict[str, VerificationCheck]:
    result: dict[str, VerificationCheck] = {}
    for check in checks:
        if check.code in result:
            raise AssertionError(f"duplicate receipt rule code: {check.code}")
        result[check.code] = check
    return result


def run_case(case: DevelopmentCase, root: Path) -> CaseResult:
    """Run one case twice and verify expectations, determinism, and privacy."""

    project = root / case.id
    _write_fixture(project, case)
    first = verify_scrna_de_preflight(project, case.contract)
    second = verify_scrna_de_preflight(project, case.contract)
    if first.model_dump(mode="json") != second.model_dump(mode="json"):
        raise AssertionError(f"{case.id}: receipt is not deterministic")

    serialized = json.dumps(first.model_dump(mode="json"), sort_keys=True)
    leaked = [canary for canary in case.privacy_canaries if canary in serialized]
    if leaked:
        raise AssertionError(f"{case.id}: privacy canary entered receipt")

    actual = l1_artifact_decision(first)
    allowed = {case.expected.l1_decision, *case.expected.allowed_l1_decisions}
    if actual not in allowed:
        raise AssertionError(
            f"{case.id}: expected L1 decision in {sorted(allowed)}, got {actual}"
        )

    by_code = _checks_by_code(first.checks)
    for code, expected in case.expected.rule_outcomes.items():
        if code not in by_code:
            raise AssertionError(f"{case.id}: expected rule {code} is absent")
        actual_outcome = by_code[code].outcome
        if actual_outcome != expected:
            raise AssertionError(
                f"{case.id}: rule {code} expected {expected.value}, got {actual_outcome.value}"
            )

    return CaseResult(
        id=case.id,
        expected=case.expected.l1_decision,
        actual=actual,
        matched=actual in allowed,
        label_review=case.label_review.status,
    )


def run_development(root: Path = CASE_ROOT) -> dict[str, object]:
    """Run all public development cases and return a deterministic aggregate report."""

    cases = load_cases(root)
    review_sheet = load_review_sheet(cases)
    baseline_protocol = load_baseline_protocol()
    with tempfile.TemporaryDirectory(prefix="omicsrepro-phase0-") as temporary:
        results = [run_case(case, Path(temporary)) for case in cases]
    decisions = Counter(result.actual for result in results)
    reviews = Counter(result.label_review for result in results)
    return {
        "schema_version": 1,
        "partition": "development",
        "contract": "scrna.de_between_conditions/v0",
        "case_count": len(results),
        "matched": sum(result.matched for result in results),
        "actual_l1_decisions": dict(sorted(decisions.items())),
        "label_review": dict(sorted(reviews.items())),
        "review_round": review_sheet.round,
        "baseline_protocol": {
            "id": baseline_protocol.id,
            "baseline_count": len(baseline_protocol.baselines),
            "network_access": baseline_protocol.network_access,
        },
        "note": "Development regression results are not a Phase 0 product claim.",
        "cases": [result.model_dump(mode="json") for result in results],
    }


def main() -> None:
    """Run the public development partition and print its JSON summary."""

    print(json.dumps(run_development(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
