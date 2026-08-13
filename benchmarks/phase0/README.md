# Phase 0 benchmark workspace

This directory contains the publishable development partition and its deterministic harness for
`scrna.de_between_conditions/v0`.

It is intentionally not the complete Phase 0 benchmark. Development cases are visible to rule
authors and therefore measure regression behavior only. Frozen evaluation cases and labels are
held separately during an active round and are released after the decision when privacy and
licensing permit.

## Run

From the repository root with OmicsRepro installed:

```bash
PYTHONPATH=src python benchmarks/phase0/run_development.py
```

The runner builds tiny synthetic H5AD projects in an operating-system temporary directory, invokes
the same verifier used by the CLI, checks expected rule outcomes and privacy canaries, and prints a
deterministic aggregate summary. It also verifies the separate label-review sheet and five-baseline
protocol. It writes nothing to external data roots.

## Add a development case

Add one YAML file to `development/cases`. Follow `case-schema.md`, use a stable case ID, and change
only the minimum evidence required to represent the failure. Do not add binary H5AD files, private
paths, real identifiers, or access-controlled data.

Every label needs independent review before it can count toward a benchmark report. Until then,
`label_review.status` must remain `pending`.

See `review/README.md` for the review packet, `baselines/README.md` for the comparator protocol, and
`frozen-evaluation-plan.md` for recruitment, custody, and unblinding boundaries. No active frozen
label belongs in this repository.
