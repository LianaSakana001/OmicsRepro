# OmicsRepro agent instructions

## Scope

Build a local-first, evidence-based reproducibility checker for omics research.

## Data safety

- Treat every external dataset root as immutable.
- Never write generated files beside source datasets.
- Write tests and reports only under the repository, a temporary directory, or an explicitly configured output directory.
- Use tiny synthetic fixtures for unit tests. Real datasets are for opt-in integration tests only.
- Do not commit omics data, credentials, access tokens, or private server paths.

## Development

- Support Python 3.11 and 3.12; use Python 3.12 for the reference development environment.
- Add deterministic tests for every check and include the evidence that caused each finding.
- Keep AI-assisted explanations optional. Core validation must work offline and deterministically.

