"""Safety checks for an opt-in external dataset mount."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

DATA_ROOT = os.environ.get("OMICSREPRO_DATA_ROOT")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not DATA_ROOT, reason="OMICSREPRO_DATA_ROOT is not configured"),
]


def test_external_data_root_is_readable_and_not_writable() -> None:
    root = Path(DATA_ROOT or "")

    assert root.is_dir()
    assert os.access(root, os.R_OK)
    assert not os.access(root, os.W_OK)

