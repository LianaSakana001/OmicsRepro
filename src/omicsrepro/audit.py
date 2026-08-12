"""Deterministic orchestration for an OmicsRepro project audit."""

from __future__ import annotations

from pathlib import Path

from omicsrepro import __version__
from omicsrepro.checks.h5ad import inspect_h5ad
from omicsrepro.config import discover_manifest, load_manifest
from omicsrepro.models import AuditReport, CheckResult, DatasetSummary, Outcome


def _resolved(root: Path, configured: str) -> Path:
    path = Path(configured).expanduser()
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _path_result(*, code: str, configured: str, resolved: Path, label: str) -> CheckResult:
    exists = resolved.is_file()
    return CheckResult(
        code=code,
        outcome=Outcome.PASS if exists else Outcome.FAIL,
        target=configured,
        message=f"{label} exists and is a regular file" if exists else f"{label} is missing",
        evidence={"configured_path": configured, "exists": exists},
        remediation=None if exists else f"Create the declared {label} or correct its path.",
    )


def audit_project(project: Path) -> AuditReport:
    """Audit one manifest and every declared path without executing project code."""

    manifest_path = discover_manifest(project)
    manifest = load_manifest(manifest_path)
    root = manifest_path.parent
    checks: list[CheckResult] = [
        CheckResult(
            code="ORP001",
            outcome=Outcome.PASS,
            target=manifest_path.name,
            message="manifest is valid against schema version 1",
            evidence={"schema_version": manifest.schema_version},
        )
    ]
    datasets: list[DatasetSummary] = []

    for item in manifest.inputs:
        resolved = _resolved(root, item.path)
        path_check = _path_result(
            code="ORP101",
            configured=item.path,
            resolved=resolved,
            label=f"input {item.id!r}",
        )
        checks.append(path_check)
        if path_check.outcome == Outcome.PASS and item.format == "h5ad":
            checks.extend(
                inspect_h5ad(
                    resolved,
                    item.checks,
                    target=item.path,
                    profile=item.profile,
                    input_id=item.id,
                    summaries=datasets,
                )
            )

    for artifact in manifest.artifacts:
        checks.append(
            _path_result(
                code="ORP201",
                configured=artifact.path,
                resolved=_resolved(root, artifact.path),
                label=f"artifact {artifact.id!r}",
            )
        )

    for step in manifest.steps:
        checks.append(
            _path_result(
                code="ORP301",
                configured=step.script,
                resolved=_resolved(root, step.script),
                label=f"step {step.id!r} script",
            )
        )

    return AuditReport.build(
        tool_version=__version__,
        project=manifest.project.name,
        manifest=manifest_path.name,
        checks=checks,
        datasets=datasets,
    )
