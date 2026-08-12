"""Built-in, versioned single-cell delivery profiles."""

from __future__ import annotations

from dataclasses import dataclass

PROFILE_VERSION = 1


@dataclass(frozen=True)
class Profile:
    """Requirements for a named H5AD delivery contract."""

    name: str
    required_obs_concepts: tuple[str, ...]
    required_var_concepts: tuple[str, ...] = ()
    require_raw_counts: bool = False
    require_embedding: bool = False


SEMANTIC_ALIASES: dict[str, tuple[str, ...]] = {
    "donor": (
        "donor_id",
        "donor",
        "Donor ID",
        "subject_id",
        "individual_id",
        "participant_id",
    ),
    "sample": (
        "sample_id",
        "sample",
        "Sample ID",
        "sample_name",
        "library_id",
        "specimen_id",
        "Specimen Barcode",
    ),
    "cell_type": (
        "cell_type",
        "celltype",
        "cell_type_annotation",
        "Cell Type",
        "cell ontology class",
        "Supertype",
        "Subclass",
        "Class",
    ),
    "batch": (
        "batch",
        "batch_id",
        "Batch",
        "sequencing_batch",
        "load_name",
        "library_id",
        "library_prep",
    ),
    "gene_id": (
        "gene_ids",
        "gene_id",
        "ensembl_id",
        "feature_id",
        "index",
    ),
}

PROFILES: dict[str, Profile] = {
    "scrna-basic": Profile(
        name="scrna-basic",
        required_obs_concepts=("donor", "sample", "cell_type"),
        require_raw_counts=True,
    ),
    "scrna-publication": Profile(
        name="scrna-publication",
        required_obs_concepts=("donor", "sample", "cell_type", "batch"),
        required_var_concepts=("gene_id",),
        require_raw_counts=True,
        require_embedding=True,
    ),
}


def aliases_for(concept: str, custom: dict[str, list[str]]) -> tuple[str, ...]:
    """Return ordered, de-duplicated built-in and project-specific aliases."""

    values = (*SEMANTIC_ALIASES[concept], *custom.get(concept, []))
    return tuple(dict.fromkeys(values))
