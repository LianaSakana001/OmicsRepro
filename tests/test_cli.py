"""CLI smoke tests."""

import json
from pathlib import Path

from typer.testing import CliRunner

from omicsrepro import __version__
from omicsrepro.cli import app

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_doctor() -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["omicsrepro"] == __version__
    assert report["python"]
    assert report["platform"]


def test_check_json_exit_zero(valid_project: Path) -> None:
    result = runner.invoke(app, ["check", str(valid_project)])

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["status"] == "pass"
    assert report["summary"]["failed"] == 0


def test_check_failure_exit_one(valid_project: Path) -> None:
    (valid_project / "data" / "input.h5ad").unlink()

    result = runner.invoke(app, ["check", str(valid_project)])

    assert result.exit_code == 1
    assert json.loads(result.stdout)["status"] == "fail"


def test_output_refuses_silent_overwrite(valid_project: Path, tmp_path: Path) -> None:
    output = tmp_path / "audit.md"
    first = runner.invoke(
        app,
        ["check", str(valid_project), "--format", "markdown", "--output", str(output)],
    )
    second = runner.invoke(
        app,
        ["check", str(valid_project), "--format", "markdown", "--output", str(output)],
    )

    assert first.exit_code == 0
    assert output.read_text(encoding="utf-8").startswith("# OmicsRepro audit report")
    assert second.exit_code == 2
    assert "use --force" in second.stderr


def test_init_refuses_existing_manifest(tmp_path: Path) -> None:
    first = runner.invoke(app, ["init", str(tmp_path)])
    second = runner.invoke(app, ["init", str(tmp_path)])

    assert first.exit_code == 0
    assert (tmp_path / "omicsrepro.yml").is_file()
    assert second.exit_code == 2
