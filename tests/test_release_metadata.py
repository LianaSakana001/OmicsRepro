"""Release metadata consistency tests."""

from __future__ import annotations

import tomllib
from pathlib import Path

import yaml

from omicsrepro import __version__

ROOT = Path(__file__).resolve().parents[1]


def test_release_version_is_synchronized() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert project["version"] == __version__
    assert citation["version"] == __version__
    assert f"## {__version__} -" in changelog


def test_public_project_metadata_uses_canonical_repository() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    repository = "https://github.com/LianaSakana001/OmicsRepro"

    assert project["urls"]["Source"] == repository
    assert citation["repository-code"] == repository
