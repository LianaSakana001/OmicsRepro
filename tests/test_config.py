"""Manifest discovery and graph validation tests."""

from pathlib import Path

import pytest

from omicsrepro.config import ManifestError, discover_manifest, load_manifest


def test_manifest_rejects_unknown_step_reference(tmp_path: Path) -> None:
    manifest = tmp_path / "omicsrepro.yml"
    manifest.write_text(
        """schema_version: 1
project:
  name: invalid-graph
inputs:
  - id: primary
    path: input.h5ad
steps:
  - id: qc
    script: qc.py
    inputs: [does-not-exist]
""",
        encoding="utf-8",
    )

    with pytest.raises(ManifestError, match="unknown inputs"):
        load_manifest(manifest)


def test_discovery_requires_exactly_one_manifest(tmp_path: Path) -> None:
    with pytest.raises(ManifestError, match="no omicsrepro.yml"):
        discover_manifest(tmp_path)

    (tmp_path / "omicsrepro.yml").write_text("{}\n", encoding="utf-8")
    (tmp_path / "omicsrepro.yaml").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ManifestError, match="multiple manifests"):
        discover_manifest(tmp_path)
