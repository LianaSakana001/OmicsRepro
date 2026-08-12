# Release process

This checklist separates reversible release preparation from tag creation and distribution. A pull
request may prepare a release, but only a maintainer deliberately creates the immutable tag and
GitHub Release after the preparation PR is merged and CI is green.

## 1. Prepare the release PR

1. Start from a clean, current `main` branch and create a dedicated release branch.
2. Choose the version according to Semantic Versioning.
3. Synchronize the version in:
   - `pyproject.toml`;
   - `src/omicsrepro/__init__.py`;
   - `CITATION.cff`;
   - the matching `CHANGELOG.md` heading.
4. Move completed entries out of `Unreleased` and record the intended release date.
5. Confirm the README describes only features that are actually present.
6. Confirm no data, credentials, access tokens, private paths, or generated reports are tracked.

## 2. Validate source and distributions

Create a release environment and run all deterministic checks:

```bash
python -m pip install -e '.[dev,omics,release]'
python -m ruff check .
python -m pytest
cffconvert --validate
python -m build
python -m twine check dist/*
```

Install the wheel into a new virtual environment rather than relying on the source checkout:

```bash
python -m venv /tmp/omicsrepro-release-smoke
/tmp/omicsrepro-release-smoke/bin/python -m pip install dist/omicsrepro-*.whl
/tmp/omicsrepro-release-smoke/bin/omicsrepro version
/tmp/omicsrepro-release-smoke/bin/omicsrepro doctor
```

The CI `package` job repeats the build, metadata check, wheel installation, and CLI smoke test.

## 3. Merge, tag, and create the GitHub Release

After review and green CI:

1. Merge the release PR without bypassing checks.
2. Verify the exact commit on `main` and repeat the package build from that commit.
3. Create one annotated tag named `vX.Y.Z` at that exact commit.
4. Push the tag without moving or replacing any existing release tag.
5. Create the GitHub Release from that tag, using the matching changelog section as release notes.
6. Attach both the wheel and source distribution and publish their SHA-256 checksums.
7. Verify the documented immutable-tag installation command in a clean environment.

If a released artifact is wrong, leave the tag immutable and publish a corrective patch release.

## 4. Python package index policy

PyPI publication is not part of the v0.2.0 release foundation. Before enabling it:

- confirm that the `omicsrepro` project name is available or select a non-conflicting distribution
  name;
- configure PyPI Trusted Publishing for a dedicated, reviewable GitHub Actions environment;
- require an immutable GitHub Release or protected tag as the workflow trigger;
- use short-lived OIDC credentials rather than a maintainer API token;
- test the complete workflow on TestPyPI first.

Never upload a distribution from an unreviewed working tree or overwrite an existing version.
