# OmicsRepro

**Local-first, evidence-based reproducibility checks for omics research.**

OmicsRepro audits the declared evidence chain from immutable source data to analysis scripts
and expected artifacts. Version 0.1 provides deterministic, read-only checks for Python and
AnnData/H5AD projects. It does not execute project scripts or upload data.

> Status: v0.1. The manifest and JSON report use schema version 1.

## What v0.1 checks

- discovery and strict validation of `omicsrepro.yml`;
- references between declared inputs, analysis steps, and output artifacts;
- existence of every declared input, script, and artifact;
- H5AD container and AnnData encoding metadata;
- `obs`, `var`, and `X` presence and shape consistency;
- required `obs` and `var` columns;
- `obs_names` and `var_names` uniqueness with a configurable safety limit;
- optional presence of `raw`;
- deterministic JSON and Markdown reports with evidence for every rule.

OmicsRepro reports evidence instead of a single opaque score. Every result contains a stable
rule code, outcome, target, message, and relevant metadata or remediation.

## Install

OmicsRepro requires Python 3.11 or 3.12.

```bash
python -m pip install -e '.[dev]'
```

The optional `omics` extra installs AnnData for integration and fixture development. The v0.1
auditor itself reads H5AD metadata with `h5py` and never loads the expression matrix into memory.

```bash
python -m pip install -e '.[dev,omics]'
```

## Quick start

Create a starter contract:

```bash
omicsrepro init my-project
```

Edit `my-project/omicsrepro.yml`, then audit it:

```bash
omicsrepro check my-project
```

JSON is written to stdout by default, which makes the command suitable for CI. To create a
human-readable report at an explicit location:

```bash
omicsrepro check my-project --format markdown --output reports/omicsrepro.md
```

OmicsRepro refuses to replace an existing report unless `--force` is supplied explicitly.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | The audit completed with no failed checks. |
| `1` | One or more reproducibility checks failed. |
| `2` | The manifest, command, or explicit report write was invalid. |

Use `--fail-on-warning` when warnings should also return exit code `1`.

## Manifest

The contract connects source data to scripts and expected artifacts without executing any of
them:

```yaml
schema_version: 1
project:
  name: example-scrna-project
inputs:
  - id: primary
    path: data/input.h5ad
    format: h5ad
    checks:
      required_obs_columns: [donor_id, cell_type]
      required_var_columns: [gene_ids]
      require_x: true
      require_raw: false
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

See [docs/manifest.md](docs/manifest.md) for the full v1 contract.

## Safety model

- Inputs are opened read-only.
- Analysis scripts are declared and checked for existence, never executed.
- Reports go only to stdout or an explicit output path.
- No network connection is used by the audit engine.
- No omics datasets, credentials, or machine-specific private paths belong in Git.
- Unit tests create tiny synthetic H5AD files in temporary directories.

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

See [docs/development.md](docs/development.md) for the local/server workflow and
[CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance.

## Scope after v0.1

Planned profiles include Seurat, workflow engines, environment lockfiles, and publication
artifact checks. Optional AI explanations may be added later; core validation will remain
offline and deterministic.

## License

Apache-2.0
