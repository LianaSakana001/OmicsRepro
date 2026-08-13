# Contributing

OmicsRepro is in alpha development. Please keep changes focused, tested, and safe for read-only
scientific data.

## Checks

```bash
ruff check .
pytest
```

Integration tests must be explicitly enabled with `OMICSREPRO_DATA_ROOT`. They must never modify the configured data root.

Changes that affect users must add an entry under `Unreleased` in `CHANGELOG.md`. Version changes
must keep `pyproject.toml`, `src/omicsrepro/__init__.py`, and `CITATION.cff` synchronized.

Experimental scientific-use contracts must also document scope, rationale, required evidence,
assurance level, known exceptions, and false-positive boundaries. Add privacy tests that prove
identifier values do not enter receipts. Missing execution evidence must remain `INDETERMINATE`.

## Phase 0 failure cases

Prefer a minimal failure case over a new feature. Development cases belong under
`benchmarks/phase0/development` and must use synthetic data or a redistributable, non-identifying
derivative. Each case needs a stable ID, scientific rationale, minimal mutation, provenance,
expected L1 decision, and expected rule outcomes. The development harness must pass before review:

```bash
PYTHONPATH=src python benchmarks/phase0/run_development.py
```

Do not commit real donor/sample identifiers, private paths, access-controlled data, or active frozen
evaluation labels. During an active benchmark round, rule authors must not inspect or tune against
the frozen evaluation partition. Case labels require independent review before they count toward a
reported benchmark.

Do not mark a label `reviewed` unless the separate review sheet records complete scientific,
rule-outcome, and privacy approval from someone other than `case_author`. Frozen cases and labels
are accepted only by the evaluation custodian outside the development checkout.

See `docs/releasing.md` for the maintainer-only release checklist. Pull requests must not create or
move release tags.
