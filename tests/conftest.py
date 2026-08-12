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
    delivery_ready: bool = False,
    missing_sample: bool = False,
    counts_shape: tuple[int, int] = (2, 2),
    count_values: tuple[tuple[float, float], tuple[float, float]] | None = None,
    embedding_shape: tuple[int, int] = (2, 2),
    design_rows: list[tuple[str, str, str, str]] | None = None,
) -> None:
    """Write only the HDF5 structures needed by the v0.1 inspector."""

    path.parent.mkdir(parents=True, exist_ok=True)
    string = h5py.string_dtype(encoding="utf-8")
    with h5py.File(path, "w") as handle:
        handle.attrs["encoding-type"] = "anndata"
        handle.attrs["encoding-version"] = "0.1.0"
        obs = handle.create_group("obs")
        obs.attrs["_index"] = "_index"
        rows = design_rows or []
        obs.create_dataset(
            "_index",
            data=(
                [f"cell-{index}" for index in range(len(rows))]
                if rows
                else ["cell-a", "cell-a" if duplicate_obs else "cell-b"]
            ),
            dtype=string,
        )
        donors = [row[2] for row in rows] if rows else ["D1", "D2"]
        obs.create_dataset("donor_id", data=donors, dtype=string)
        if delivery_ready:
            obs.create_dataset(
                "sample_id",
                data=["S1", "" if missing_sample else "S2"],
                dtype=string,
            )
            cell_type = obs.create_group("cell_type")
            cell_type.attrs["encoding-type"] = "categorical"
            cell_type.attrs["encoding-version"] = "0.2.0"
            cell_type.create_dataset("categories", data=["T cell", "B cell"], dtype=string)
            cell_type.create_dataset("codes", data=[0, 1], dtype="int8")
            obs.create_dataset("batch", data=["batch-1", "batch-2"], dtype=string)
        if rows:
            obs.create_dataset("cell_type", data=[row[0] for row in rows], dtype=string)
            obs.create_dataset("disease", data=[row[1] for row in rows], dtype=string)
            obs.create_dataset("sample_id", data=[row[3] for row in rows], dtype=string)
        var = handle.create_group("var")
        var.attrs["_index"] = "_index"
        var.create_dataset("_index", data=["GENE1", "GENE2"], dtype=string)
        var.create_dataset("gene_ids", data=["ENSG1", "ENSG2"], dtype=string)
        handle.create_dataset("X", shape=x_shape, dtype="float32")
        if delivery_ready:
            layers = handle.create_group("layers")
            if count_values is None:
                counts = layers.create_dataset("counts", shape=counts_shape, dtype="int32")
                if counts_shape[0] and counts_shape[1]:
                    counts[0, 0] = 1
            else:
                layers.create_dataset("counts", data=count_values, dtype="float32")
            obsm = handle.create_group("obsm")
            obsm.create_dataset("X_umap", shape=embedding_shape, dtype="float32")


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


@pytest.fixture
def publication_project(tmp_path: Path) -> Path:
    """Create a minimal scRNA-seq object satisfying the publication profile."""

    project = tmp_path / "publication-project"
    write_h5ad(project / "data" / "input.h5ad", delivery_ready=True)
    (project / "omicsrepro.yml").write_text(
        """schema_version: 1
project:
  name: publication-fixture
inputs:
  - id: primary
    path: data/input.h5ad
    format: h5ad
    profile: scrna-publication
    checks:
      unique_obs_names: true
      unique_var_names: true
""",
        encoding="utf-8",
    )
    return project
