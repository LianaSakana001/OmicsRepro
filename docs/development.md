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
- an external dataset root such as `/data/public-omics` with read-only access.

Run the opt-in safety test before any dataset integration test. Select one explicit H5AD file so
the integration run remains bounded:

```bash
OMICSREPRO_DATA_ROOT=/data/public-omics \
OMICSREPRO_H5AD=/data/public-omics/path/to/example.h5ad \
pytest -m integration
```

All generated fixtures, caches, and reports must stay under `/workspace` or a temporary directory.
Server development deployments must not copy or modify `.git`; Git operations happen in the local
development checkout.

Phase 0 server runs may inspect only explicitly selected public H5AD files under the read-only mount.
Contracts, derived privacy-safe fixtures, receipts, benchmark tables, and caches must stay under the
writable OmicsRepro project directory. The default verifier must not download data, run notebooks,
or execute analysis scripts; any future opt-in runner requires a separate security review.
