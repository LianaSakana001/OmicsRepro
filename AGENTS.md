# OmicsRepro agent instructions

## Scope

Build a local-first, evidence-based reproducibility checker for omics research.

OmicsRepro verifies explicit, versioned conditions supported by inspectable evidence. It does not
certify biological truth, replace statistical or domain review, or claim that an analysis is valid
when required evidence is unavailable.

## Data safety

- Treat every external dataset root as immutable.
- Never write generated files beside source datasets.
- Write tests and reports only under the repository, a temporary directory, or an explicitly configured output directory.
- Use tiny synthetic fixtures for unit tests. Real datasets are for opt-in integration tests only.
- Do not commit omics data, credentials, access tokens, or private server paths.
- Keep artifact inspection read-only. Never execute a declared project script in the core verifier.
- Put any future execution capture or independent recomputation in a separately reviewed, sandboxed
  adapter; it must not silently broaden core verifier permissions.
- Treat missing evidence as `INDETERMINATE`, not `PASS`.

## Development

- Support Python 3.11 and 3.12; use Python 3.12 for the reference development environment.
- Add deterministic tests for every check and include the evidence that caused each finding.
- Keep AI-assisted explanations optional. Core validation must work offline and deterministically.
- Preserve the stable `check` command and audit schema while experimental verification contracts
  evolve behind a separate receipt schema.
- Every scientific contract must document its scope, rationale, required evidence, false-positive
  boundary, known exceptions, assurance level, and version.
- Treat public Phase 0 development cases as visible regression fixtures, never as proof of product
  advantage. Do not inspect or tune against an active frozen evaluation partition.
- Benchmark fixtures must be synthetic or explicitly redistributable and non-identifying. Keep
  private paths, real identifiers, frozen labels, and external omics data out of Git.
