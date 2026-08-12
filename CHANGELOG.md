# Changelog

All notable changes to OmicsRepro are documented in this file. The project follows Semantic
Versioning while it develops its public manifest, report, and adapter contracts.

## Unreleased

### Added

- Experimental `scrna.de_between_conditions/v0` artifact-level preflight and receipt schema.
- Explicit assurance levels and fail-closed `INDETERMINATE` / `NOT_APPLICABLE` outcomes.
- Phase 0 falsification benchmark, product responsibility, and safety boundaries.
- Versioned product charter and a machine-checked Phase 0 development-corpus harness.

### Security

- Scientific-use receipts expose aggregate mapping-conflict and replicate counts, never donor or
  sample identifiers.
- Experimental verification remains read-only and does not execute analysis code.

## 0.2.0 - 2026-08-12

### Added

- Release validation for wheel and source distributions.
- Standard software citation and maintainer release documentation.
- Versioned `scrna-basic` and `scrna-publication` delivery profiles.
- Semantic matching for donor, sample, cell type, batch, and gene identifiers.
- Bounded, privacy-preserving metadata completeness and cardinality checks.
- Validation of raw-count candidates in AnnData `raw` and conventional layers.
- Observation-compatible UMAP, t-SNE, and PCA checks.
- Dataset delivery summaries in report schema version 2.
- Machine-readable profile discovery through `omicsrepro profiles`.

### Changed

- Explicitly support Python 3.11 and 3.12.
- Preserve manifest schema version 1 compatibility for projects without a profile.

### Security

- Sparse matrices are sampled without densification.
- Metadata and matrix scans use explicit limits.
- Reports include aggregate evidence and field names, never category values or identifiers.

## 0.1.0 - 2026-08-12

### Added

- Strict `omicsrepro.yml` project contracts.
- Deterministic, read-only H5AD structure checks.
- JSON and Markdown reports with stable exit codes.
- `omicsrepro init`, `check`, `doctor`, and `version` commands.
- Unit, CLI, graph, and opt-in real-data integration tests.
