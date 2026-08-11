"""Data models shared by the deterministic audit engine."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Outcome(StrEnum):
    """Outcome of one reproducibility check."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class CheckResult(BaseModel):
    """One evidence-bearing check result."""

    model_config = ConfigDict(frozen=True)

    code: str
    outcome: Outcome
    message: str
    target: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    remediation: str | None = None


class AuditSummary(BaseModel):
    """Counts used by humans and CI callers."""

    model_config = ConfigDict(frozen=True)

    passed: int
    warnings: int
    failed: int
    total: int


class AuditReport(BaseModel):
    """Stable, machine-readable v1 audit report."""

    model_config = ConfigDict(frozen=True)

    schema_version: int = 1
    tool_version: str
    project: str
    manifest: str
    status: str
    summary: AuditSummary
    checks: list[CheckResult]

    @classmethod
    def build(
        cls,
        *,
        tool_version: str,
        project: str,
        manifest: str,
        checks: list[CheckResult],
    ) -> AuditReport:
        """Create a report without timestamps so identical inputs stay deterministic."""

        passed = sum(item.outcome == Outcome.PASS for item in checks)
        warnings = sum(item.outcome == Outcome.WARN for item in checks)
        failed = sum(item.outcome == Outcome.FAIL for item in checks)
        return cls(
            tool_version=tool_version,
            project=project,
            manifest=manifest,
            status="fail" if failed else "pass",
            summary=AuditSummary(
                passed=passed,
                warnings=warnings,
                failed=failed,
                total=len(checks),
            ),
            checks=checks,
        )
