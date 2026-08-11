# Manifest schema v1

`omicsrepro.yml` is a strict, versioned contract. Unknown fields and broken graph references are
configuration errors rather than silently ignored metadata.

## Top-level fields

| Field | Required | Meaning |
|---|---|---|
| `schema_version` | yes | Must be `1`. |
| `project.name` | yes | Human-readable project name. |
| `inputs` | yes | One or more immutable source datasets. |
| `artifacts` | no | Expected output files such as tables or figures. |
| `steps` | no | Analysis scripts and their declared input/output IDs. |

IDs start with a letter and may contain letters, numbers, `_`, `-`, and `.`. IDs must be unique
within their collection. A step input references an input or artifact ID; a step output references
an artifact ID. OmicsRepro validates these links but never imports or executes the script.

Paths may be relative to the manifest directory or absolute. This permits source datasets to stay
outside the code repository on a read-only mount. Reports are not written beside inputs unless the
user explicitly selects such a path.

## H5AD input checks

Each v0.1 input has `format: h5ad` and supports:

| Field | Default | Meaning |
|---|---:|---|
| `required_obs_columns` | `[]` | Required observation annotations. |
| `required_var_columns` | `[]` | Required variable annotations. |
| `require_x` | `true` | Require an expression matrix. |
| `require_raw` | `false` | Require an AnnData `raw` snapshot. |
| `unique_obs_names` | `true` | Check observation index uniqueness. |
| `unique_var_names` | `true` | Check variable index uniqueness. |
| `max_index_values` | `1000000` | Exact uniqueness safety limit per axis. |

When an index exceeds `max_index_values`, OmicsRepro returns a warning instead of allocating an
unbounded in-memory set. Increase the limit deliberately if an exact check is required for a larger
dataset.

## Complete example

```yaml
schema_version: 1
project:
  name: example-scrna-project
inputs:
  - id: primary
    path: /read-only/public-data/example.h5ad
    format: h5ad
    checks:
      required_obs_columns:
        - donor_id
        - cell_type
      required_var_columns:
        - gene_ids
      require_x: true
      require_raw: false
      unique_obs_names: true
      unique_var_names: true
      max_index_values: 1000000
artifacts:
  - id: qc_table
    path: results/qc.tsv
    kind: table
  - id: overview
    path: figures/overview.png
    kind: figure
steps:
  - id: qc
    script: scripts/qc.py
    inputs: [primary]
    outputs: [qc_table, overview]
```

## Rule families

- `ORP0xx`: project and manifest checks;
- `ORP1xx`: declared input paths;
- `ORP2xx`: declared artifact paths;
- `ORP3xx`: declared analysis scripts;
- `H5AD0xx`: AnnData/H5AD structure and semantic metadata.

Rule codes remain stable within schema version 1. New backward-compatible rules may be added in
v0.x releases.
