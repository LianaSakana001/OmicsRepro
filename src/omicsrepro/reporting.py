"""Deterministic JSON and Markdown report rendering."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from omicsrepro.models import AuditReport


def render_json(report: AuditReport) -> str:
    """Render stable JSON suitable for CI and downstream tooling."""

    return json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"


def _cell(value: str | None) -> str:
    return (value or "").replace("|", "\\|").replace("\n", " ")


def render_markdown(report: AuditReport) -> str:
    """Render a compact evidence report for maintainers."""

    lines = [
        "# OmicsRepro audit report",
        "",
        f"- Project: `{report.project}`",
        f"- Manifest: `{report.manifest}`",
        f"- Tool version: `{report.tool_version}`",
        f"- Status: **{report.status.upper()}**",
        (
            f"- Summary: {report.summary.passed} passed, "
            f"{report.summary.warnings} warnings, {report.summary.failed} failed"
        ),
    ]
    if report.datasets:
        lines.extend(["", "## Dataset delivery summary", ""])
        for dataset in report.datasets:
            profile = dataset.profile or "custom"
            dimensions = f"{dataset.observations} × {dataset.variables}"
            lines.extend(
                [
                    f"### {_cell(dataset.input_id)}",
                    "",
                    f"- Format: `{dataset.format}`",
                    f"- Profile: `{profile}`",
                    f"- Dimensions: `{dimensions}`",
                    (
                        f"- Raw counts: `{dataset.raw_count_location or 'not validated'}` "
                        f"({'validated' if dataset.raw_counts_validated else 'not validated'})"
                    ),
                    (
                        "- Semantic columns: "
                        + (
                            ", ".join(
                                f"`{concept}={column}`"
                                for concept, column in sorted(dataset.semantic_columns.items())
                            )
                            or "none"
                        )
                    ),
                    (
                        "- Embeddings: "
                        + (", ".join(f"`{item}`" for item in dataset.embeddings) or "none")
                    ),
                    "",
                ]
            )

    lines.extend(["## Checks", "", "| Outcome | Rule | Target | Message |", "|---|---|---|---|"])
    for item in report.checks:
        lines.append(
            f"| {item.outcome.value.upper()} | `{item.code}` | "
            f"`{_cell(item.target)}` | {_cell(item.message)} |"
        )

    details = [item for item in report.checks if item.evidence or item.remediation]
    if details:
        lines.extend(["", "## Evidence", ""])
    for item in details:
        lines.extend([f"### {item.code}: {_cell(item.target)}", ""])
        if item.evidence:
            lines.extend(
                ["```json", json.dumps(item.evidence, indent=2, sort_keys=True), "```", ""]
            )
        if item.remediation:
            lines.extend([f"Remediation: {item.remediation}", ""])
    return "\n".join(lines).rstrip() + "\n"


def write_report(path: Path, content: str, *, force: bool = False) -> None:
    """Write only to an explicitly selected path and refuse silent overwrites."""

    destination = path.expanduser()
    if destination.exists() and not force:
        raise FileExistsError(f"report already exists: {destination}; use --force to replace it")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=destination.parent,
        prefix=f".{destination.name}.",
        delete=False,
    ) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    try:
        os.replace(temporary, destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
