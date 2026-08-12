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

See `docs/releasing.md` for the maintainer-only release checklist. Pull requests must not create or
move release tags.
