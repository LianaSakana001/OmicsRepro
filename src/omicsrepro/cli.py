"""Command-line interface for OmicsRepro."""

from __future__ import annotations

import json
import platform

import typer

from omicsrepro import __version__

app = typer.Typer(
    add_completion=False,
    help="Local-first reproducibility checks for omics research.",
    no_args_is_help=True,
)


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


if __name__ == "__main__":
    app()

