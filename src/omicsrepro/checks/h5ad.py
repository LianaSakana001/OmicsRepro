"""Read-only structural and semantic checks for AnnData H5AD files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import h5py
import numpy as np

from omicsrepro.config import H5ADCheckSpec
from omicsrepro.models import CheckResult, DatasetSummary, Outcome
from omicsrepro.profiles import PROFILE_VERSION, PROFILES, aliases_for

RAW_LAYER_ALIASES = ("counts", "raw_counts", "raw-counts", "raw", "umis", "umi")
EMBEDDING_ALIASES = ("x_umap", "umap", "x_tsne", "tsne", "x_pca", "pca")
SCAN_CHUNK_SIZE = 100_000


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


def _raw_count_shape(handle: h5py.File, location: str | None) -> tuple[int, int] | None:
    """Resolve raw/X separately because AnnData raw may retain additional variables."""

    if location == "raw":
        raw = handle.get("raw")
        return _matrix_shape(raw.get("X")) if isinstance(raw, h5py.Group) else None
    return _matrix_shape(handle.get(location)) if location else None


def _matrix_values(node: h5py.Dataset | h5py.Group | None) -> h5py.Dataset | None:
    """Return dense values or sparse stored values without densifying the matrix."""

    if isinstance(node, h5py.Dataset):
        return node
    if isinstance(node, h5py.Group):
        data = node.get("data")
        return data if isinstance(data, h5py.Dataset) else None
    return None


def _raw_count_evidence(
    handle: h5py.File, location: str | None, *, max_values: int
) -> dict[str, Any]:
    """Bounded sample evidence that a claimed raw-count matrix is count-like."""

    if location == "raw":
        raw = handle.get("raw")
        node = raw.get("X") if isinstance(raw, h5py.Group) else None
    else:
        node = handle.get(location) if location else None
    values = _matrix_values(node)
    if values is None:
        return {"sampled_values": 0, "reason": "matrix values are not accessible"}

    if len(values.shape) == 1:
        sample = values[: min(max_values, int(values.shape[0]))]
    elif len(values.shape) == 2:
        columns = int(values.shape[1])
        if columns >= max_values:
            sample = values[:1, :max_values].reshape(-1)
        else:
            rows = max(1, min(int(values.shape[0]), max_values // max(columns, 1)))
            sample = values[:rows, :].reshape(-1)
    else:
        return {"sampled_values": 0, "reason": "matrix encoding has unsupported rank"}
    sample = np.asarray(sample)[:max_values]
    if sample.size == 0:
        return {
            "sampled_values": 0,
            "dtype": str(values.dtype),
            "non_negative": True,
            "finite": True,
            "integer_like": True,
            "has_positive": False,
        }
    finite = bool(np.all(np.isfinite(sample)))
    non_negative = bool(np.all(sample >= 0)) if finite else False
    integer_like = bool(np.all(np.abs(sample - np.rint(sample)) <= 1e-6)) if finite else False
    has_positive = bool(np.any(sample > 0)) if finite else False
    return {
        "sampled_values": int(sample.size),
        "dtype": str(values.dtype),
        "non_negative": non_negative,
        "finite": finite,
        "integer_like": integer_like,
        "has_positive": has_positive,
    }


def _raw_count_candidates(has_raw: bool, layer_names: list[str]) -> list[str]:
    """Return deterministic candidates, preferring AnnData raw then known layer names."""

    candidates = ["raw"] if has_raw else []
    accepted = {_normalized(alias) for alias in RAW_LAYER_ALIASES}
    candidates.extend(f"layers/{name}" for name in layer_names if _normalized(name) in accepted)
    return candidates


def _select_raw_counts(
    handle: h5py.File,
    candidates: list[str],
    *,
    obs_count: int | None,
    var_count: int | None,
    max_values: int,
) -> tuple[str | None, tuple[int, int] | None, dict[str, Any], list[dict[str, Any]]]:
    """Select the first shape-compatible, count-like candidate and record every attempt."""

    attempted: list[dict[str, Any]] = []
    for location in candidates:
        shape = _raw_count_shape(handle, location)
        value_sample = _raw_count_evidence(handle, location, max_values=max_values)
        shape_valid = (
            shape is not None
            and shape[0] == obs_count
            and (shape[1] == var_count if location != "raw" else shape[1] > 0)
        )
        values_valid = all(
            value_sample.get(key) is True
            for key in ("non_negative", "finite", "integer_like", "has_positive")
        )
        attempted.append(
            {
                "location": location,
                "shape": shape,
                "shape_valid": shape_valid,
                "value_sample": value_sample,
                "values_valid": values_valid,
            }
        )
        if shape_valid and values_valid:
            return location, shape, value_sample, attempted
    if attempted:
        last = attempted[-1]
        return None, last["shape"], last["value_sample"], attempted
    return None, None, {"sampled_values": 0, "reason": "no candidate found"}, attempted


def _normalized(value: str) -> str:
    return "".join(character.lower() for character in value if character.isalnum())


def _match_column(available: list[str], aliases: tuple[str, ...]) -> str | None:
    """Match exact names first, then normalized names without leaking values."""

    for alias in aliases:
        if alias in available:
            return alias
    by_normalized = {_normalized(item): item for item in available}
    for alias in aliases:
        if match := by_normalized.get(_normalized(alias)):
            return match
    return None


def _decode_scalar(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value.item() if hasattr(value, "item") else value


def _is_missing(value: Any) -> bool:
    value = _decode_scalar(value)
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip() or value.strip().lower() in {"na", "nan", "none", "null"}
    try:
        return bool(np.isnan(value))
    except TypeError:
        return False


def _column_quality(
    node: h5py.Dataset | h5py.Group,
    *,
    row_count: int | None,
    max_values: int,
    max_categories: int,
) -> dict[str, Any]:
    """Collect bounded, privacy-preserving completeness and cardinality counts."""

    if row_count is None:
        return {"scanned": False, "reason": "axis index is invalid"}
    if row_count > max_values:
        return {
            "scanned": False,
            "reason": "column exceeds max_column_values",
            "rows": row_count,
            "max_column_values": max_values,
        }

    missing = 0
    categories: set[Any] = set()
    categories_truncated = False
    categorical = isinstance(node, h5py.Group) and isinstance(node.get("codes"), h5py.Dataset)
    values: h5py.Dataset | None
    if categorical:
        codes = node.get("codes")
        assert isinstance(codes, h5py.Dataset)
        values = codes
        category_node = node.get("categories")
        category_count = (
            int(category_node.shape[0]) if isinstance(category_node, h5py.Dataset) else None
        )
        if len(values.shape) != 1 or int(values.shape[0]) != row_count:
            return {
                "scanned": False,
                "reason": "column length does not match axis",
                "rows": row_count,
                "column_values": int(values.shape[0]) if values.shape else None,
            }
        used_codes: set[int] = set()
        for start in range(0, row_count, SCAN_CHUNK_SIZE):
            chunk = values[start : min(start + SCAN_CHUNK_SIZE, row_count)]
            missing += int(np.count_nonzero(chunk < 0))
            used_codes.update(int(code) for code in np.unique(chunk) if code >= 0)
        return {
            "scanned": True,
            "rows": row_count,
            "missing_values": missing,
            "missing_fraction": round(missing / row_count, 6) if row_count else 0.0,
            "categories": len(used_codes),
            "declared_categories": category_count,
            "categorical": True,
        }

    values = node if isinstance(node, h5py.Dataset) and len(node.shape) == 1 else None
    if values is None:
        return {"scanned": False, "reason": "unsupported column encoding", "rows": row_count}
    if int(values.shape[0]) != row_count:
        return {
            "scanned": False,
            "reason": "column length does not match axis",
            "rows": row_count,
            "column_values": int(values.shape[0]),
        }
    for start in range(0, row_count, SCAN_CHUNK_SIZE):
        for value in values[start : min(start + SCAN_CHUNK_SIZE, row_count)]:
            if _is_missing(value):
                missing += 1
                continue
            decoded = _decode_scalar(value)
            if decoded in categories:
                continue
            if len(categories) < max_categories:
                categories.add(decoded)
            else:
                categories_truncated = True
    return {
        "scanned": True,
        "rows": row_count,
        "missing_values": missing,
        "missing_fraction": round(missing / row_count, 6) if row_count else 0.0,
        "categories": len(categories),
        "categories_truncated": categories_truncated,
        "categorical": False,
    }


def _quality_result(
    *,
    concept: str,
    column: str,
    node: h5py.Dataset | h5py.Group,
    row_count: int | None,
    spec: H5ADCheckSpec,
    target: str,
) -> CheckResult:
    evidence = {
        "concept": concept,
        "column": column,
        **_column_quality(
            node,
            row_count=row_count,
            max_values=spec.max_column_values,
            max_categories=spec.max_categories,
        ),
    }
    problems: list[str] = []
    if not evidence["scanned"]:
        problems.append(str(evidence["reason"]))
    if evidence.get("missing_values", 0):
        problems.append("contains missing values")
    if evidence.get("categories") in {0, 1}:
        problems.append("has fewer than two non-missing categories")
    if evidence.get("categories_truncated"):
        problems.append("category counting reached max_categories")
    return CheckResult(
        code="H5AD104",
        outcome=Outcome.WARN if problems else Outcome.PASS,
        target=target,
        message=(
            f"semantic {concept!r} column passed bounded quality checks"
            if not problems
            else f"semantic {concept!r} column needs review: {'; '.join(problems)}"
        ),
        evidence=evidence,
        remediation=(
            None
            if not problems
            else "Review missing values and category structure, or raise scan limits explicitly."
        ),
    )


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


def inspect_h5ad(
    path: Path,
    spec: H5ADCheckSpec,
    *,
    target: str,
    profile: str | None = None,
    input_id: str = "input",
    summaries: list[DatasetSummary] | None = None,
) -> list[CheckResult]:
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

        layers = handle.get("layers")
        layer_names = (
            sorted(str(key) for key in layers.keys())
            if isinstance(layers, h5py.Group)
            else []
        )
        obsm = handle.get("obsm")
        embedding_names = (
            sorted(str(key) for key in obsm.keys()) if isinstance(obsm, h5py.Group) else []
        )
        raw_count_candidates = _raw_count_candidates(has_raw, layer_names)
        raw_count_location: str | None = None
        raw_count_shape: tuple[int, int] | None = None
        count_evidence: dict[str, Any] = {}
        attempted_candidates: list[dict[str, Any]] = []
        if profile is not None and PROFILES[profile].require_raw_counts:
            (
                raw_count_location,
                raw_count_shape,
                count_evidence,
                attempted_candidates,
            ) = _select_raw_counts(
                handle,
                raw_count_candidates,
                obs_count=obs_count,
                var_count=var_count,
                max_values=spec.max_matrix_sample_values,
            )

        semantic_columns: dict[str, str] = {}
        if profile is not None:
            selected = PROFILES[profile]
            obs_names = sorted(str(key) for key in obs.keys())
            var_names = sorted(str(key) for key in var.keys())
            missing_obs: list[str] = []
            for concept in selected.required_obs_concepts:
                match = _match_column(obs_names, aliases_for(concept, spec.semantic_aliases))
                if match is None:
                    missing_obs.append(concept)
                else:
                    semantic_columns[concept] = match
            results.append(
                CheckResult(
                    code="H5AD101",
                    outcome=Outcome.FAIL if missing_obs else Outcome.PASS,
                    target=target,
                    message=(
                        "required semantic obs fields are present"
                        if not missing_obs
                        else "required semantic obs fields are missing"
                    ),
                    evidence={
                        "profile": profile,
                        "profile_version": PROFILE_VERSION,
                        "matched": semantic_columns,
                        "missing_concepts": missing_obs,
                    },
                    remediation=(
                        None
                        if not missing_obs
                        else "Add suitable obs fields or declare project-specific semantic_aliases."
                    ),
                )
            )

            missing_var: list[str] = []
            for concept in selected.required_var_concepts:
                match = _match_column(var_names, aliases_for(concept, spec.semantic_aliases))
                if match is None:
                    missing_var.append(concept)
                else:
                    semantic_columns[concept] = match
            if selected.required_var_concepts:
                results.append(
                    CheckResult(
                        code="H5AD102",
                        outcome=Outcome.FAIL if missing_var else Outcome.PASS,
                        target=target,
                        message=(
                            "required semantic var fields are present"
                            if not missing_var
                            else "required semantic var fields are missing"
                        ),
                        evidence={"matched": semantic_columns, "missing_concepts": missing_var},
                        remediation=(
                            None
                            if not missing_var
                            else "Add stable gene identifiers or declare a gene_id alias."
                        ),
                    )
                )

            if selected.require_raw_counts:
                results.append(
                    CheckResult(
                        code="H5AD103",
                        outcome=Outcome.PASS if raw_count_location is not None else Outcome.FAIL,
                        target=target,
                        message=(
                            "a raw-count representation matches obs and var"
                            if raw_count_location is not None
                            else "a shape-compatible, count-like raw representation is missing"
                        ),
                        evidence={
                            "location": raw_count_location,
                            "shape": raw_count_shape,
                            "expected_shape": (obs_count, var_count),
                            "accepted_layer_names": sorted(RAW_LAYER_ALIASES),
                            "value_sample": count_evidence,
                            "attempted_candidates": attempted_candidates,
                        },
                        remediation=(
                            None
                            if raw_count_location is not None
                            else (
                                "Preserve raw counts in raw or a conventionally named "
                                "counts/UMIs layer."
                            )
                        ),
                    )
                )

            if selected.require_embedding:
                matched_embeddings: list[str] = []
                invalid_embeddings: list[str] = []
                if isinstance(obsm, h5py.Group):
                    for name in embedding_names:
                        if _normalized(name) not in {
                            _normalized(alias) for alias in EMBEDDING_ALIASES
                        }:
                            continue
                        shape = _matrix_shape(obsm.get(name))
                        if shape is not None and shape[0] == obs_count and shape[1] >= 2:
                            matched_embeddings.append(name)
                        else:
                            invalid_embeddings.append(name)
                results.append(
                    CheckResult(
                        code="H5AD105",
                        outcome=Outcome.PASS if matched_embeddings else Outcome.FAIL,
                        target=target,
                        message=(
                            "a publication-ready embedding is present"
                            if matched_embeddings
                            else "no shape-compatible publication embedding was found"
                        ),
                        evidence={
                            "matched": matched_embeddings,
                            "invalid": invalid_embeddings,
                            "accepted_names": sorted(EMBEDDING_ALIASES),
                        },
                        remediation=(
                            None
                            if matched_embeddings
                            else (
                                "Store UMAP, t-SNE, or PCA coordinates in obsm with all "
                                "observations."
                            )
                        ),
                    )
                )

            for concept in selected.required_obs_concepts:
                if column := semantic_columns.get(concept):
                    node = obs.get(column)
                    if isinstance(node, (h5py.Dataset, h5py.Group)):
                        results.append(
                            _quality_result(
                                concept=concept,
                                column=column,
                                node=node,
                                row_count=obs_count,
                                spec=spec,
                                target=target,
                            )
                        )

        if summaries is not None:
            summaries.append(
                DatasetSummary(
                    input_id=input_id,
                    format="h5ad",
                    profile=profile,
                    observations=obs_count,
                    variables=var_count,
                    layers=layer_names,
                    embeddings=embedding_names,
                    raw_count_location=raw_count_location,
                    raw_counts_validated=raw_count_location is not None,
                    semantic_columns=semantic_columns,
                )
            )
    return results
