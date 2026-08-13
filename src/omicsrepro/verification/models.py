"""Stable, evidence-bearing models for experimental verification receipts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class VerificationOutcome(StrEnum):
    """Outcome of a verification check or receipt."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    INDETERMINATE = "indeterminate"
    NOT_APPLICABLE = "not_applicable"


class AssuranceLevel(StrEnum):
    """Strongest evidence source used by a receipt, ordered from L1 to L4."""

    ARTIFACT_INSPECTION = "artifact_inspection"
    DECLARED_EVIDENCE = "declared_evidence"
    INSTRUMENTED_EXECUTION = "instrumented_execution"
    INDEPENDENT_RECOMPUTATION = "independent_recomputation"


class VerificationCheck(BaseModel):
    """One deterministic contract check and the evidence behind it."""

    model_config = ConfigDict(frozen=True)

    code: str
    outcome: VerificationOutcome
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    remediation: str | None = None


class VerificationSummary(BaseModel):
    """Counts for every supported verification outcome."""

    model_config = ConfigDict(frozen=True)

    passed: int
    warnings: int
    failed: int
    indeterminate: int
    not_applicable: int
    total: int


class VerificationReceipt(BaseModel):
    """Machine-readable receipt for one contract evaluation."""

    model_config = ConfigDict(frozen=True)

    schema_version: Literal[1] = 1
    tool_version: str
    contract: str
    contract_status: Literal["experimental", "stable"]
    project: str
    subject: dict[str, str]
    verdict: VerificationOutcome
    assurance: AssuranceLevel
    summary: VerificationSummary
    checks: list[VerificationCheck]
    limitations: list[str] = Field(default_factory=list)

    @classmethod
    def build(
        cls,
        *,
        tool_version: str,
        contract: str,
        contract_status: Literal["experimental", "stable"],
        project: str,
        subject: dict[str, str],
        assurance: AssuranceLevel,
        checks: list[VerificationCheck],
        limitations: list[str] | None = None,
    ) -> VerificationReceipt:
        """Build a deterministic receipt with fail-closed verdict precedence."""

        if not checks:
            raise ValueError("a verification receipt requires at least one check")
        counts = {
            outcome: sum(item.outcome == outcome for item in checks)
            for outcome in VerificationOutcome
        }
        if counts[VerificationOutcome.FAIL]:
            verdict = VerificationOutcome.FAIL
        elif counts[VerificationOutcome.INDETERMINATE] or (
            counts[VerificationOutcome.NOT_APPLICABLE] == len(checks)
        ):
            verdict = VerificationOutcome.INDETERMINATE
        elif counts[VerificationOutcome.WARN]:
            verdict = VerificationOutcome.WARN
        else:
            verdict = VerificationOutcome.PASS
        return cls(
            tool_version=tool_version,
            contract=contract,
            contract_status=contract_status,
            project=project,
            subject=subject,
            verdict=verdict,
            assurance=assurance,
            summary=VerificationSummary(
                passed=counts[VerificationOutcome.PASS],
                warnings=counts[VerificationOutcome.WARN],
                failed=counts[VerificationOutcome.FAIL],
                indeterminate=counts[VerificationOutcome.INDETERMINATE],
                not_applicable=counts[VerificationOutcome.NOT_APPLICABLE],
                total=len(checks),
            ),
            checks=checks,
            limitations=limitations or [],
        )
