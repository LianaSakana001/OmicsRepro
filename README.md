# OmicsRepro

**Local-first reproducibility checks for omics research.**

OmicsRepro is an open-source command-line tool for validating the evidence chain from source data and software environments to analysis steps, tables, and figures. The core engine is deterministic and works offline; optional AI assistance may explain findings or propose fixes later.

> Status: pre-alpha project scaffold. The first profile will target single-cell RNA-seq projects using Python, Scanpy, and AnnData.

## Design principles

- **Evidence over scores:** every finding identifies the file, rule, evidence, and remediation.
- **Domain-aware checks:** validate omics artifacts and provenance, not only repository hygiene.
- **Local-first:** unpublished code and data do not need to leave the user's machine.
- **Read-only inputs:** source datasets are immutable; reports go to a separate output directory.
- **Cross-ecosystem roadmap:** Python/AnnData first, then R/Seurat and workflow engines.

## Quick start

```bash
conda env create -f environment.yml
conda activate omicsrepro-py312
omicsrepro doctor
pytest
```

For editable installation into an existing Python 3.11 or 3.12 environment:

```bash
python -m pip install -e '.[dev,omics]'
```

## Development and testing

Unit tests use small synthetic fixtures and run locally and in CI. Real public datasets are used only by opt-in integration tests through `OMICSREPRO_DATA_ROOT`.

```bash
OMICSREPRO_DATA_ROOT=/path/to/read-only/data pytest -m integration
```

See [docs/development.md](docs/development.md) for the local/server workflow.

## License

Apache-2.0

