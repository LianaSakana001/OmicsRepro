# Contributing

OmicsRepro is in pre-alpha development. Please keep changes focused, tested, and safe for read-only scientific data.

## Checks

```bash
ruff check .
pytest
```

Integration tests must be explicitly enabled with `OMICSREPRO_DATA_ROOT`. They must never modify the configured data root.

