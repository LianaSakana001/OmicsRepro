"""Read bounded metadata facts from H5AD without exposing identifier values."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import h5py
import numpy as np

CHUNK_SIZE = 100_000


class UnsupportedColumnEncoding(ValueError):
    """Raised when v0 cannot deterministically read an H5AD metadata column."""


def _text(value: Any) -> str | None:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if hasattr(value, "item"):
        value = value.item()
    if value is None:
        return None
    text = str(value).strip()
    return None if not text or text.lower() in {"na", "nan", "none", "null"} else text


def _column_length(node: h5py.Dataset | h5py.Group) -> int:
    if isinstance(node, h5py.Dataset) and len(node.shape) == 1:
        return int(node.shape[0])
    if isinstance(node, h5py.Group):
        codes = node.get("codes")
        if isinstance(codes, h5py.Dataset) and len(codes.shape) == 1:
            return int(codes.shape[0])
    raise UnsupportedColumnEncoding("expected a one-dimensional dataset or categorical column")


def iter_column(
    node: h5py.Dataset | h5py.Group, *, max_categories: int
) -> Iterator[str | None]:
    """Yield decoded values for plain or AnnData categorical columns in bounded chunks."""

    length = _column_length(node)
    if isinstance(node, h5py.Dataset):
        for start in range(0, length, CHUNK_SIZE):
            for value in node[start : min(start + CHUNK_SIZE, length)]:
                yield _text(value)
        return

    codes = node.get("codes")
    categories = node.get("categories")
    if not isinstance(codes, h5py.Dataset) or not isinstance(categories, h5py.Dataset):
        raise UnsupportedColumnEncoding("categorical column lacks codes or categories")
    if len(categories.shape) != 1 or int(categories.shape[0]) > max_categories:
        raise UnsupportedColumnEncoding("categorical dictionary exceeds the safety limit")
    decoded_categories = [_text(value) for value in categories[...]]
    for start in range(0, length, CHUNK_SIZE):
        for value in codes[start : min(start + CHUNK_SIZE, length)]:
            code = int(np.asarray(value).item())
            if code < 0:
                yield None
            elif code >= len(decoded_categories):
                raise UnsupportedColumnEncoding("categorical code exceeds declared categories")
            else:
                yield decoded_categories[code]


def column_length(node: h5py.Dataset | h5py.Group) -> int:
    """Return the number of observations represented by a supported column."""

    return _column_length(node)
