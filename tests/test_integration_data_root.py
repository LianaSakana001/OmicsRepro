"""Safety checks for an opt-in external dataset mount."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from omicsrepro.checks.h5ad import inspect_h5ad
from omicsrepro.config import H5ADCheckSpec
from omicsrepro.models import Outcome

DATA_ROOT = os.environ.get("OMICSREPRO_DATA_ROOT")
H5AD_PATH = os.environ.get("OMICSREPRO_H5AD")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not DATA_ROOT, reason="OMICSREPRO_DATA_ROOT is not configured"),
]


def test_external_data_root_is_readable_and_not_writable() -> None:
    root = Path(DATA_ROOT or "")

    assert root.is_dir()
    assert os.access(root, os.R_OK)
    assert not os.access(root, os.W_OK)


@pytest.mark.skipif(not H5AD_PATH, reason="OMICSREPRO_H5AD is not configured")
def test_real_h5ad_metadata_is_readable_without_loading_x() -> None:
    path = Path(H5AD_PATH or "")
    root = Path(DATA_ROOT or "")

    assert path.is_file()
    assert path.is_relative_to(root)
    results = inspect_h5ad(
        path,
        H5ADCheckSpec(unique_obs_names=False, unique_var_names=False),
        target=path.name,
    )

    readable = next(item for item in results if item.code == "H5AD001")
    assert readable.outcome == Outcome.PASS
