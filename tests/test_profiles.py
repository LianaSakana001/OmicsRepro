"""Built-in single-cell delivery profile tests."""

from __future__ import annotations

from pathlib import Path

from conftest import write_h5ad

from omicsrepro.audit import audit_project
from omicsrepro.models import Outcome
from omicsrepro.reporting import render_markdown


def _by_code(report: object, code: str) -> list[object]:
    return [item for item in report.checks if item.code == code]  # type: ignore[attr-defined]


def test_publication_profile_passes_and_summarizes(publication_project: Path) -> None:
    report = audit_project(publication_project)

    assert report.status == "pass"
    assert report.schema_version == 2
    assert all(item.outcome == Outcome.PASS for item in _by_code(report, "H5AD101"))
    assert all(item.outcome == Outcome.PASS for item in _by_code(report, "H5AD102"))
    assert all(item.outcome == Outcome.PASS for item in _by_code(report, "H5AD103"))
    assert all(item.outcome == Outcome.PASS for item in _by_code(report, "H5AD105"))
    assert len(_by_code(report, "H5AD104")) == 4
    summary = report.datasets[0]
    assert summary.profile == "scrna-publication"
    assert summary.raw_count_location == "layers/counts"
    assert summary.raw_counts_validated is True
    assert summary.semantic_columns == {
        "batch": "batch",
        "cell_type": "cell_type",
        "donor": "donor_id",
        "gene_id": "gene_ids",
        "sample": "sample_id",
    }
    assert "Dataset delivery summary" in render_markdown(report)


def test_profile_missing_concepts_and_raw_counts_fail(valid_project: Path) -> None:
    manifest = valid_project / "omicsrepro.yml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            "    format: h5ad", "    format: h5ad\n    profile: scrna-basic"
        ),
        encoding="utf-8",
    )

    report = audit_project(valid_project)
    semantics = _by_code(report, "H5AD101")[0]
    raw_counts = _by_code(report, "H5AD103")[0]

    assert report.status == "fail"
    assert semantics.outcome == Outcome.FAIL
    assert semantics.evidence["missing_concepts"] == ["sample", "cell_type"]
    assert raw_counts.outcome == Outcome.FAIL


def test_metadata_missing_value_is_privacy_preserving_warning(
    publication_project: Path,
) -> None:
    write_h5ad(
        publication_project / "data" / "input.h5ad",
        delivery_ready=True,
        missing_sample=True,
    )

    report = audit_project(publication_project)
    sample = next(
        item
        for item in _by_code(report, "H5AD104")
        if item.evidence["concept"] == "sample"
    )

    assert report.status == "pass"
    assert sample.outcome == Outcome.WARN
    assert sample.evidence["missing_values"] == 1
    assert sample.evidence["missing_fraction"] == 0.5
    assert "S1" not in str(sample.evidence)


def test_invalid_counts_and_embedding_shapes_fail(publication_project: Path) -> None:
    write_h5ad(
        publication_project / "data" / "input.h5ad",
        delivery_ready=True,
        counts_shape=(1, 2),
        embedding_shape=(1, 2),
    )

    report = audit_project(publication_project)

    assert _by_code(report, "H5AD103")[0].outcome == Outcome.FAIL
    assert _by_code(report, "H5AD105")[0].outcome == Outcome.FAIL


def test_normalized_values_are_not_accepted_as_raw_counts(publication_project: Path) -> None:
    write_h5ad(
        publication_project / "data" / "input.h5ad",
        delivery_ready=True,
        count_values=((0.0, 1.25), (2.0, 3.0)),
    )

    report = audit_project(publication_project)
    counts = _by_code(report, "H5AD103")[0]

    assert counts.outcome == Outcome.FAIL
    assert counts.evidence["value_sample"]["integer_like"] is False
    assert counts.evidence["value_sample"]["sampled_values"] == 4
    assert counts.evidence["attempted_candidates"][0]["location"] == "layers/counts"


def test_empty_matrix_is_not_accepted_as_raw_counts(publication_project: Path) -> None:
    write_h5ad(
        publication_project / "data" / "input.h5ad",
        delivery_ready=True,
        count_values=((0.0, 0.0), (0.0, 0.0)),
    )

    counts = _by_code(audit_project(publication_project), "H5AD103")[0]

    assert counts.outcome == Outcome.FAIL
    assert counts.evidence["value_sample"]["has_positive"] is False


def test_invalid_raw_falls_back_to_valid_counts_layer(publication_project: Path) -> None:
    import h5py

    path = publication_project / "data" / "input.h5ad"
    with h5py.File(path, "r+") as handle:
        raw = handle.create_group("raw")
        raw.create_dataset("X", shape=(1, 2), dtype="int32")

    report = audit_project(publication_project)
    counts = _by_code(report, "H5AD103")[0]

    assert counts.outcome == Outcome.PASS
    assert counts.evidence["location"] == "layers/counts"
    assert [item["location"] for item in counts.evidence["attempted_candidates"]] == [
        "raw",
        "layers/counts",
    ]


def test_custom_semantic_alias_extends_profile(tmp_path: Path) -> None:
    project = tmp_path / "alias-project"
    write_h5ad(project / "input.h5ad", delivery_ready=True)
    with __import__("h5py").File(project / "input.h5ad", "r+") as handle:
        handle["obs"].move("donor_id", "participant_code")
    (project / "omicsrepro.yml").write_text(
        """schema_version: 1
project:
  name: alias-fixture
inputs:
  - id: primary
    path: input.h5ad
    profile: scrna-basic
    checks:
      semantic_aliases:
        donor: [participant_code]
""",
        encoding="utf-8",
    )

    report = audit_project(project)

    assert _by_code(report, "H5AD101")[0].outcome == Outcome.PASS
    assert report.datasets[0].semantic_columns["donor"] == "participant_code"


def test_column_scan_limit_warns_without_reading_values(publication_project: Path) -> None:
    manifest = publication_project / "omicsrepro.yml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            "      unique_obs_names: true",
            "      unique_obs_names: true\n      max_column_values: 1",
        ),
        encoding="utf-8",
    )

    report = audit_project(publication_project)

    quality = _by_code(report, "H5AD104")
    assert len(quality) == 4
    assert all(item.outcome == Outcome.WARN for item in quality)
    assert all(item.evidence["scanned"] is False for item in quality)


def test_categorical_cardinality_is_bounded(publication_project: Path) -> None:
    manifest = publication_project / "omicsrepro.yml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            "      unique_obs_names: true",
            "      unique_obs_names: true\n      max_categories: 1",
        ),
        encoding="utf-8",
    )

    report = audit_project(publication_project)
    cell_type = next(
        item
        for item in _by_code(report, "H5AD104")
        if item.evidence["concept"] == "cell_type"
    )

    assert cell_type.outcome == Outcome.WARN
    assert cell_type.evidence["categories"] == 1
    assert cell_type.evidence["declared_categories"] == 2
    assert cell_type.evidence["categories_truncated"] is True
