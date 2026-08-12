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

See `docs/releasing.md` for the maintainer-only release checklist. Pull requests must not create or
move release tags.
