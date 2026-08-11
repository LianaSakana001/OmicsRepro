"""CLI smoke tests."""

import json

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

