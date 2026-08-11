# Development workflow

OmicsRepro uses three testing layers:

1. Local unit tests with tiny synthetic data.
2. GitHub Actions using the same deterministic fixtures.
3. Opt-in server integration tests against public datasets mounted read-only.

## Reference environment

```bash
conda env create -f environment.yml
conda activate omicsrepro-py312
ruff check .
pytest
```

## Server integration contract

The container must expose:

- the repository at `/workspace` with read/write access;
- an external dataset root at `/data/New_NeuroDataHub` with read-only access.

Run the opt-in safety test before any dataset integration test:

```bash
OMICSREPRO_DATA_ROOT=/data/New_NeuroDataHub pytest -m integration
```

All generated fixtures, caches, and reports must stay under `/workspace` or a temporary directory.

