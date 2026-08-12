"""Command-line interface for OmicsRepro."""

from __future__ import annotations

import json
import platform
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from omicsrepro import __version__
from omicsrepro.audit import audit_project
from omicsrepro.config import ManifestError
from omicsrepro.profiles import PROFILE_VERSION, PROFILES, SEMANTIC_ALIASES
from omicsrepro.reporting import render_json, render_markdown, write_report
from omicsrepro.verification.config import (
    VerificationContractError,
    load_verification_contract,
)
from omicsrepro.verification.models import VerificationOutcome
from omicsrepro.verification.scrna_de import verify_scrna_de_preflight

app = typer.Typer(
    add_completion=False,
    help="Local-first reproducibility checks for omics research.",
    no_args_is_help=True,
)


class ReportFormat(StrEnum):
    """Supported deterministic output formats."""

    json = "json"
    markdown = "markdown"


@app.command("version")
def show_version() -> None:
    """Print the installed OmicsRepro version."""

    typer.echo(__version__)


@app.command()
def doctor() -> None:
    """Report the runtime used for local checks."""

    report = {
        "omicsrepro": __version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
    }
    typer.echo(json.dumps(report, indent=2, sort_keys=True))


@app.command("profiles")
def show_profiles() -> None:
    """Print the built-in single-cell delivery profiles as JSON."""

    payload = {
        "profile_version": PROFILE_VERSION,
        "profiles": {
            name: {
                "required_obs_concepts": profile.required_obs_concepts,
                "required_var_concepts": profile.required_var_concepts,
                "require_raw_counts": profile.require_raw_counts,
                "require_embedding": profile.require_embedding,
            }
            for name, profile in sorted(PROFILES.items())
        },
        "semantic_aliases": {
            name: values for name, values in sorted(SEMANTIC_ALIASES.items())
        },
    }
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


@app.command("init")
def init_project(
    directory: Annotated[
        Path, typer.Argument(help="Directory that will receive omicsrepro.yml.")
    ] = Path("."),
) -> None:
    """Create a minimal manifest without overwriting existing files."""

    target = directory.expanduser() / "omicsrepro.yml"
    if target.exists():
        typer.echo(f"error: manifest already exists: {target}", err=True)
        raise typer.Exit(code=2)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        """schema_version: 1
project:
  name: my-omics-project
inputs:
  - id: primary
    path: data/example.h5ad
    format: h5ad
    checks:
      required_obs_columns: []
      required_var_columns: []
      require_x: true
      require_raw: false
      unique_obs_names: true
      unique_var_names: true
    profile: scrna-basic
""",
        encoding="utf-8",
    )
    typer.echo(str(target))


@app.command("check")
def check_project(
    project: Annotated[
        Path, typer.Argument(help="Project directory or explicit omicsrepro.yml path.")
    ] = Path("."),
    report_format: Annotated[
        ReportFormat,
        typer.Option("--format", help="Report format written to stdout or --output."),
    ] = ReportFormat.json,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Explicit report path; stdout is used by default."),
    ] = None,
    force: Annotated[
        bool, typer.Option(help="Replace an existing explicit report path.")
    ] = False,
    fail_on_warning: Annotated[
        bool, typer.Option(help="Return exit code 1 when the report contains warnings.")
    ] = False,
) -> None:
    """Audit a project without executing its scripts or modifying its inputs."""

    try:
        report = audit_project(project)
        content = (
            render_json(report)
            if report_format == ReportFormat.json
            else render_markdown(report)
        )
        if output is None:
            typer.echo(content, nl=False)
        else:
            write_report(output, content, force=force)
            typer.echo(f"wrote {output}", err=True)
    except (ManifestError, OSError, FileExistsError) as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    if report.summary.failed or (fail_on_warning and report.summary.warnings):
        raise typer.Exit(code=1)


@app.command("verify")
def verify_project(
    project: Annotated[
        Path, typer.Argument(help="Project directory or explicit omicsrepro.yml path.")
    ],
    contract_file: Annotated[
        Path,
        typer.Option(
            "--contract-file",
            help="YAML declaration for an experimental scientific-use contract.",
        ),
    ],
) -> None:
    """Run a read-only experimental scientific-use contract and emit a JSON receipt."""

    try:
        contract = load_verification_contract(contract_file)
        receipt = verify_scrna_de_preflight(project, contract)
        typer.echo(
            json.dumps(receipt.model_dump(mode="json"), indent=2, sort_keys=True),
        )
    except (ManifestError, VerificationContractError, OSError) as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    if receipt.verdict == VerificationOutcome.FAIL:
        raise typer.Exit(code=1)
    if receipt.verdict == VerificationOutcome.INDETERMINATE:
        raise typer.Exit(code=3)


if __name__ == "__main__":
    app()
