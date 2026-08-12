"""Tiny deterministic H5AD fixtures for unit tests."""

from __future__ import annotations

from pathlib import Path

import h5py
import pytest


def write_h5ad(
    path: Path,
    *,
    duplicate_obs: bool = False,
    x_shape: tuple[int, int] = (2, 2),
) -> None:
    """Write only the HDF5 structures needed by the v0.1 inspector."""

    path.parent.mkdir(parents=True, exist_ok=True)
    string = h5py.string_dtype(encoding="utf-8")
    with h5py.File(path, "w") as handle:
        handle.attrs["encoding-type"] = "anndata"
        handle.attrs["encoding-version"] = "0.1.0"
        obs = handle.create_group("obs")
        obs.attrs["_index"] = "_index"
        obs.create_dataset(
            "_index",
            data=["cell-a", "cell-a" if duplicate_obs else "cell-b"],
            dtype=string,
        )
        obs.create_dataset("donor_id", data=["D1", "D2"], dtype=string)
        var = handle.create_group("var")
        var.attrs["_index"] = "_index"
        var.create_dataset("_index", data=["GENE1", "GENE2"], dtype=string)
        var.create_dataset("gene_ids", data=["ENSG1", "ENSG2"], dtype=string)
        handle.create_dataset("X", shape=x_shape, dtype="float32")


@pytest.fixture
def valid_project(tmp_path: Path) -> Path:
    """Create a complete project contract with one input, step, and artifact."""

    project = tmp_path / "project"
    write_h5ad(project / "data" / "input.h5ad")
    (project / "scripts").mkdir()
    (project / "scripts" / "qc.py").write_text("# declared, never executed\n", encoding="utf-8")
    (project / "results").mkdir()
    (project / "results" / "qc.tsv").write_text("metric\tvalue\n", encoding="utf-8")
    (project / "omicsrepro.yml").write_text(
        """schema_version: 1
project:
  name: fixture-project
inputs:
  - id: primary
    path: data/input.h5ad
    format: h5ad
    checks:
      required_obs_columns: [donor_id]
      required_var_columns: [gene_ids]
artifacts:
  - id: qc_table
    path: results/qc.tsv
    kind: table
steps:
  - id: qc
    script: scripts/qc.py
    inputs: [primary]
    outputs: [qc_table]
""",
        encoding="utf-8",
    )
    return project
