# Security policy

## Supported versions

Security fixes are applied to the latest released v0.x version while the project is pre-1.0.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting for this repository. Do not include private
omics data, credentials, patient information, or unpublished datasets in a report. A minimal
synthetic reproduction is strongly preferred.

## Data-safety guarantees

The deterministic audit engine opens declared inputs read-only, does not execute declared analysis
scripts, and does not require network access. Report files are created only when the caller provides
an explicit output path. Single-cell metadata reports contain aggregate completeness/cardinality
counts but never category values, donor identifiers, or sample identifiers. Experimental
scientific-use receipts follow the same boundary: they report only aggregate mapping conflicts and
replicate counts from inspected metadata. A receipt repeats population and condition labels that
the user explicitly placed in the contract, but never emits scanned donor/sample identifiers or
undeclared category values. Missing or unsupported evidence produces `INDETERMINATE` rather than a
permissive pass.

Any future execution-capture or independent-recomputation adapter is outside the default verifier's
trust boundary and requires a separate threat model, sandbox, resource policy, and review before it
can be enabled.
