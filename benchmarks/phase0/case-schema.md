# Phase 0 development case schema

Each `development/cases/*.yml` file is a complete, synthetic case definition consumed by
`run_development.py`. Unknown keys fail validation.

## Required fields

| Field | Meaning |
|---|---|
| `schema_version` | Case schema version; currently `1` |
| `id` | Stable lowercase ID such as `p0-dev-001` |
| `partition` | Must be `development` in this repository |
| `class` | `pass`, `fail`, `near_miss`, `ambiguous`, `decoy`, `corrupted`, or `stale` |
| `failure_family` | Narrow family represented by the case |
| `severity` | `control`, `low`, `medium`, or `high` |
| `title`, `rationale`, `case_author` | Human-reviewable purpose, reasoning, and label proposer |
| `provenance` | Must declare `kind: synthetic`, generator, and a non-identifying license |
| `fixture` | Tiny design rows and count-matrix behavior used to derive H5AD at runtime |
| `contract` | Complete `scrna.de_between_conditions/v0` declaration |
| `expected` | Expected L1 decision plus rule outcomes |
| `privacy_canaries` | Synthetic identifiers that must not occur in the receipt |
| `label_review` | Independent review state and reviewer |

`fixture.design_rows` use the order `[population, condition, donor, sample]`. Empty strings model
missing values. `fixture.counts.mode` is one of:

- `valid`: shape-compatible, non-negative integer counts with positive evidence;
- `absent`: no accepted raw-count candidate;
- `non_integer`: a conventional counts layer contains non-integer values.
- `shape_mismatch`: a count-like layer does not match the observation axis.

## Expected L1 decision

The public receipt remains `INDETERMINATE` when execution evidence is absent. To score only the
artifact-inspection claim, the development harness excludes `ORV190` and projects remaining checks:

- any `FAIL` -> `fail`;
- otherwise any `INDETERMINATE` -> `indeterminate`;
- otherwise -> `pass` (warnings remain non-blocking).

This projection is benchmark metadata, not a new product verdict.

## Review rules

- Start with `label_review.status: pending` and `reviewer: null`.
- A reviewer must understand the represented scientific failure and must not equal `case_author`.
- Ambiguous cases must list `expected.allowed_l1_decisions` and explain why one deterministic label
  would be misleading.
- A case copied from public evidence must not use this synthetic schema without documenting the
  derivation and compatible redistribution terms.
