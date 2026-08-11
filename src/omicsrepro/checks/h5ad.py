"""Read-only structural and semantic checks for AnnData H5AD files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import h5py

from omicsrepro.config import H5ADCheckSpec
from omicsrepro.models import CheckResult, Outcome


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _frame_index(group: h5py.Group) -> h5py.Dataset | None:
    key = _text(group.attrs.get("_index")) or "_index"
    node = group.get(key)
    return node if isinstance(node, h5py.Dataset) else None


def _matrix_shape(node: h5py.Dataset | h5py.Group | None) -> tuple[int, int] | None:
    if isinstance(node, h5py.Dataset) and len(node.shape) == 2:
        return int(node.shape[0]), int(node.shape[1])
    if isinstance(node, h5py.Group):
        shape = node.attrs.get("shape")
        if shape is not None and len(shape) == 2:
            return int(shape[0]), int(shape[1])
    return None


def _index_uniqueness(
    *,
    dataset: h5py.Dataset | None,
    code: str,
    axis: str,
    target: str,
    limit: int,
) -> CheckResult:
    if dataset is None or len(dataset.shape) != 1:
        return CheckResult(
            code=code,
            outcome=Outcome.FAIL,
            target=target,
            message=f"{axis} index dataset is missing or not one-dimensional",
            remediation=f"Write a valid AnnData {axis} index before exporting the H5AD file.",
        )

    count = int(dataset.shape[0])
    if count > limit:
        return CheckResult(
            code=code,
            outcome=Outcome.WARN,
            target=target,
            message=f"{axis} index uniqueness was not checked because it exceeds the safety limit",
            evidence={"index_values": count, "max_index_values": limit},
            remediation=(
                "Increase max_index_values explicitly if an exact uniqueness check is required."
            ),
        )

    values = dataset[...]
    seen: set[bytes | str] = set()
    duplicate: str | None = None
    for value in values:
        normalized: bytes | str
        if isinstance(value, bytes):
            normalized = value
        elif hasattr(value, "tobytes"):
            normalized = value.tobytes()
        else:
            normalized = str(value)
        if normalized in seen:
            duplicate = _text(value)
            break
        seen.add(normalized)

    if duplicate is not None:
        return CheckResult(
            code=code,
            outcome=Outcome.FAIL,
            target=target,
            message=f"{axis} index contains duplicate values",
            evidence={"first_duplicate": duplicate, "index_values": count},
            remediation=f"Make {axis}_names unique and regenerate the H5AD file.",
        )
    return CheckResult(
        code=code,
        outcome=Outcome.PASS,
        target=target,
        message=f"{axis} index is unique",
        evidence={"index_values": count},
    )


def inspect_h5ad(path: Path, spec: H5ADCheckSpec, *, target: str) -> list[CheckResult]:
    """Inspect HDF5 metadata without materializing the expression matrix."""

    results: list[CheckResult] = []
    try:
        handle = h5py.File(path, "r")
    except (OSError, ValueError) as exc:
        return [
            CheckResult(
                code="H5AD001",
                outcome=Outcome.FAIL,
                target=target,
                message="file is not a readable HDF5/H5AD container",
                evidence={"error": str(exc)},
                remediation="Provide an intact H5AD file readable by h5py.",
            )
        ]

    with handle:
        results.append(
            CheckResult(
                code="H5AD001",
                outcome=Outcome.PASS,
                target=target,
                message="file is a readable HDF5 container",
            )
        )

        encoding_type = _text(handle.attrs.get("encoding-type"))
        encoding_version = _text(handle.attrs.get("encoding-version"))
        if encoding_type == "anndata":
            outcome = Outcome.PASS
            message = "root metadata declares an AnnData object"
            remediation = None
        elif encoding_type is None:
            outcome = Outcome.WARN
            message = "root AnnData encoding metadata is absent"
            remediation = "Re-export with a current anndata version to record encoding metadata."
        else:
            outcome = Outcome.FAIL
            message = "root object is not encoded as AnnData"
            remediation = "Provide an H5AD file whose root encoding-type is 'anndata'."
        results.append(
            CheckResult(
                code="H5AD002",
                outcome=outcome,
                target=target,
                message=message,
                evidence={"encoding_type": encoding_type, "encoding_version": encoding_version},
                remediation=remediation,
            )
        )

        obs = handle.get("obs")
        var = handle.get("var")
        axes_valid = isinstance(obs, h5py.Group) and isinstance(var, h5py.Group)
        results.append(
            CheckResult(
                code="H5AD003",
                outcome=Outcome.PASS if axes_valid else Outcome.FAIL,
                target=target,
                message=(
                    "obs and var annotation tables are present"
                    if axes_valid
                    else "obs or var annotation table is missing"
                ),
                evidence={
                    "has_obs": isinstance(obs, h5py.Group),
                    "has_var": isinstance(var, h5py.Group),
                },
                remediation=(
                    None
                    if axes_valid
                    else "Export an AnnData object with valid obs and var tables."
                ),
            )
        )
        if not axes_valid:
            return results
        assert isinstance(obs, h5py.Group)
        assert isinstance(var, h5py.Group)

        obs_index = _frame_index(obs)
        var_index = _frame_index(var)
        obs_count = int(obs_index.shape[0]) if obs_index is not None else None
        var_count = int(var_index.shape[0]) if var_index is not None else None
        matrix = handle.get("X")
        matrix_shape = _matrix_shape(matrix)

        if matrix is None and not spec.require_x:
            x_outcome = Outcome.PASS
            x_message = "X is absent and the manifest permits metadata-only AnnData"
            x_remediation = None
        elif matrix is None:
            x_outcome = Outcome.FAIL
            x_message = "required expression matrix X is missing"
            x_remediation = (
                "Store X or set require_x: false for an intentional metadata-only object."
            )
        elif matrix_shape is None:
            x_outcome = Outcome.FAIL
            x_message = "expression matrix X has no readable two-dimensional shape"
            x_remediation = "Re-export X as a dense or AnnData-compatible sparse matrix."
        elif obs_count is None or var_count is None:
            x_outcome = Outcome.FAIL
            x_message = "matrix shape cannot be compared because an axis index is invalid"
            x_remediation = "Repair the obs and var index datasets."
        elif matrix_shape != (obs_count, var_count):
            x_outcome = Outcome.FAIL
            x_message = "X shape is inconsistent with obs and var"
            x_remediation = "Regenerate the AnnData object with aligned observations and variables."
        else:
            x_outcome = Outcome.PASS
            x_message = "X shape matches obs and var"
            x_remediation = None
        results.append(
            CheckResult(
                code="H5AD004",
                outcome=x_outcome,
                target=target,
                message=x_message,
                evidence={"x_shape": matrix_shape, "obs_rows": obs_count, "var_rows": var_count},
                remediation=x_remediation,
            )
        )

        for code, group, required, label in (
            ("H5AD005", obs, spec.required_obs_columns, "obs"),
            ("H5AD006", var, spec.required_var_columns, "var"),
        ):
            available = sorted(str(key) for key in group.keys())
            missing = sorted(set(required) - set(available))
            results.append(
                CheckResult(
                    code=code,
                    outcome=Outcome.FAIL if missing else Outcome.PASS,
                    target=target,
                    message=(
                        f"required {label} columns are present"
                        if not missing
                        else f"required {label} columns are missing"
                    ),
                    evidence={"required": sorted(required), "missing": missing},
                    remediation=(
                        None
                        if not missing
                        else f"Add the missing {label} columns or correct the manifest contract."
                    ),
                )
            )

        if spec.unique_obs_names:
            results.append(
                _index_uniqueness(
                    dataset=obs_index,
                    code="H5AD007",
                    axis="obs",
                    target=target,
                    limit=spec.max_index_values,
                )
            )
        if spec.unique_var_names:
            results.append(
                _index_uniqueness(
                    dataset=var_index,
                    code="H5AD008",
                    axis="var",
                    target=target,
                    limit=spec.max_index_values,
                )
            )

        has_raw = isinstance(handle.get("raw"), h5py.Group)
        results.append(
            CheckResult(
                code="H5AD009",
                outcome=Outcome.FAIL if spec.require_raw and not has_raw else Outcome.PASS,
                target=target,
                message=(
                    "raw is present"
                    if has_raw
                    else (
                        "required raw snapshot is missing"
                        if spec.require_raw
                        else "raw snapshot is not required"
                    )
                ),
                evidence={"has_raw": has_raw, "required": spec.require_raw},
                remediation=(
                    "Preserve raw counts in adata.raw or set require_raw: false explicitly."
                    if spec.require_raw and not has_raw
                    else None
                ),
            )
        )
    return results
