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
an explicit output path.
