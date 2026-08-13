# OmicsRepro

**Evidence-based preflight for single-cell data delivery and experimental scientific-use
verification.**

OmicsRepro audits the evidence chain from immutable source data to analysis scripts and expected
artifacts. It provides deterministic, local-first checks for Python and AnnData/H5AD projects. It
does not execute project scripts, load the full expression matrix, upload data, or require network
access.

> Status: the stable v0.2 code is available on `main`, but no immutable `v0.2.0` release has been
> published yet. The manifest remains schema version 1; JSON and Markdown audit reports use schema
> version 2.

The post-v0.2 experimental track evaluates narrow scientific-use contracts. Experimental receipts
report `INDETERMINATE` when the available evidence cannot support a claim; they do not certify
biological truth or replace expert statistical review.

OmicsRepro is currently running a Phase 0 falsification study: can a deterministic verifier catch
silent scientific failures more reliably than a strong Agent with expert instructions? Read the
[product charter](docs/product-charter.md) and [benchmark protocol](docs/phase0-benchmark.md) before
interpreting the experimental track as a product claim.

## The problem

A project can contain code and an H5AD file yet still be difficult to reuse. The deposited object
may omit donor, sample, batch, or cell-type annotations; raw counts may have been overwritten;
embeddings may be absent; or the final figure may no longer be connected to a declared script and
artifact. OmicsRepro turns those implicit expectations into an executable contract before data are
handed to a collaborator, submitted to a repository, or attached to a publication.

## What v0.2 checks

- strict discovery and validation of `omicsrepro.yml`;
- declared input, analysis-step, and artifact references and paths;
- H5AD container, AnnData encoding, `obs`, `var`, and `X` structure;
- matrix/axis shape consistency and unique observation/variable names;
- explicit required `obs` and `var` columns;
- semantic single-cell fields through common aliases and project-specific extensions;
- bounded completeness and cardinality checks without exposing metadata values;
- raw-count availability in `raw` or conventionally named `layers`;
- bounded evidence that a raw-count representation is finite, non-negative, and integer-like;
- publication embeddings such as UMAP, t-SNE, or PCA with compatible dimensions;
- deterministic JSON and Markdown reports with a delivery summary and evidence per rule.

## Install

OmicsRepro requires Python 3.11 or 3.12.

Until the first tagged release is published, early adopters can install the current public source:

```bash
python -m pip install \
  "omicsrepro @ git+https://github.com/LianaSakana001/OmicsRepro.git@main"
```

After the `v0.2.0` tag is published, use the immutable release tag instead:

```bash
python -m pip install \
  "omicsrepro @ git+https://github.com/LianaSakana001/OmicsRepro.git@v0.2.0"
```

Then verify the installation:

```bash
omicsrepro version
omicsrepro doctor
```

For development, clone the repository and install the editable test environment:

```bash
python -m pip install -e '.[dev]'
```

The optional `omics` extra installs AnnData for integration and fixture development. The auditor
itself reads H5AD metadata with `h5py` and never materializes `X`.

```bash
python -m pip install -e '.[dev,omics]'
```

## Quick start

Create a starter contract using the `scrna-basic` profile:

```bash
omicsrepro init my-project
```

Edit `my-project/omicsrepro.yml`, then audit it:

```bash
omicsrepro check my-project
```

JSON is written to stdout by default for CI. To create a human-readable delivery report:

```bash
omicsrepro check my-project --format markdown --output reports/omicsrepro.md
```

OmicsRepro refuses to replace an existing report unless `--force` is supplied explicitly.

## Which command should I use?

| Command | Status | Use it for | It does not claim |
|---|---|---|---|
| `omicsrepro check` | Stable v0.2 behavior | H5AD delivery, structure, metadata, count, embedding, and declared artifact preflight | That a scientific analysis was executed correctly |
| `omicsrepro verify` | Experimental Phase 0 | A declared `scrna.de_between_conditions/v0` artifact-level preflight | That aggregation, model design, contrast, method, or results were verified |

The experimental verifier is deliberately fail-closed. A clean artifact-level preflight still
returns `INDETERMINATE` for execution claims until separately reviewed execution evidence exists.
See [docs/contracts/scrna-de-between-conditions-v0.md](docs/contracts/scrna-de-between-conditions-v0.md)
for the exact contract.

## Profiles

Profiles express domain requirements without forcing every project to use identical column names.
Inspect the versioned profile definitions and built-in aliases with:

```bash
omicsrepro profiles
```

| Profile | Intended use | Requirements |
|---|---|---|
| `scrna-basic` | Internal handoff and routine reuse | donor, sample, cell type, and raw counts |
| `scrna-publication` | Publication or public-data preflight | basic requirements plus batch, gene IDs, and an embedding |

Common aliases such as `donor_id`, `Donor ID`, `cell_type`, `Subclass`, `counts`, and `UMIs` are
supported. Projects can extend aliases explicitly:

```yaml
checks:
  semantic_aliases:
    donor: [participant_code]
    cell_type: [final_annotation]
```

See [docs/profiles.md](docs/profiles.md) for severity and privacy behavior.

## Manifest example

```yaml
schema_version: 1
project:
  name: example-scrna-project
inputs:
  - id: primary
    path: data/input.h5ad
    format: h5ad
    profile: scrna-publication
    checks:
      required_obs_columns: [disease]
      required_var_columns: [feature_types]
      semantic_aliases:
        donor: [participant_code]
artifacts:
  - id: qc_table
    path: results/qc.tsv
    kind: table
steps:
  - id: qc
    script: scripts/qc.py
    inputs: [primary]
    outputs: [qc_table]
```

The profile and explicit `checks` are additive. See [docs/manifest.md](docs/manifest.md) for the
full contract.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Audit completed without failures; warnings may remain. |
| `1` | One or more checks failed, or `--fail-on-warning` was selected. |
| `2` | Manifest, command, or explicit report write was invalid. |

The experimental `verify` command also uses exit code `3` when the receipt is
`INDETERMINATE`. See [docs/verification-boundaries.md](docs/verification-boundaries.md) before using
experimental contracts in CI.

## Safety model

- Inputs are opened read-only.
- Analysis scripts are declared and checked for existence, never executed.
- Reports go only to stdout or an explicit output path.
- No network connection is used by the audit engine.
- Large indexes and metadata columns have configurable scan limits.
- Raw-count evidence uses a bounded sample and never densifies sparse matrices.
- Reports expose column names and aggregate counts, not donor, sample, or cell-type values.
- No omics datasets, credentials, or machine-specific private paths belong in Git.

## Development and testing

```bash
ruff check .
pytest
```

Real public datasets are opt-in integration tests through read-only environment variables:

```bash
OMICSREPRO_DATA_ROOT=/path/to/read-only/data \
OMICSREPRO_H5AD=/path/to/read-only/data/example.h5ad \
pytest -m integration
```

See [docs/development.md](docs/development.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Participate in Phase 0

The most useful contribution is a small, reviewable failure case—not another broad feature. Good
cases represent a silent error that could survive a successful analysis run, such as a donor mapped
to two conditions, a sample mapped to two donors, an insufficient replicate design, an unsuitable
matrix, or ambiguous metadata.

Public contributions must use synthetic data or redistributable, non-identifying derivatives. Do
not submit private omics files, donor/sample identifiers, credentials, or machine-specific paths.
The repository contains a machine-checked development corpus under
[`benchmarks/phase0`](benchmarks/phase0); frozen evaluation labels remain outside the development
branch until a benchmark round is complete.

## Citation

If OmicsRepro contributes to a dataset delivery, publication, or reproducibility review, cite the
software and the exact version used. GitHub renders the repository's
[`CITATION.cff`](CITATION.cff) through **Cite this repository**. A DOI will only be added if a
versioned software archive is deposited; none is claimed for v0.2.0.

Release changes are recorded in [CHANGELOG.md](CHANGELOG.md). Maintainer release checks are
documented in [docs/releasing.md](docs/releasing.md).

## Scope after v0.2

The next phase is evidence-gated rather than format-gated. OmicsRepro will first benchmark a narrow
single-cell differential-expression preflight against realistic silent failures and strong Agent +
expert-instruction baselines. Seurat, additional omics, execution adapters, and UI work remain
candidate expansions only after real failure cases justify them. See
[docs/phase0-benchmark.md](docs/phase0-benchmark.md). The governing product scope and stop/pivot
conditions are recorded in [docs/product-charter.md](docs/product-charter.md).

## License

Apache-2.0
