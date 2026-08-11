"""Manifest discovery and validation for ``omicsrepro.yml``."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

MANIFEST_NAMES = ("omicsrepro.yml", "omicsrepro.yaml")
IDENTIFIER_PATTERN = r"^[A-Za-z][A-Za-z0-9_.-]*$"


class ManifestError(ValueError):
    """Raised when a project manifest cannot be discovered or validated."""


class ProjectSpec(BaseModel):
    """Human-facing project metadata."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)


class H5ADCheckSpec(BaseModel):
    """Domain-aware checks applied without loading the expression matrix."""

    model_config = ConfigDict(extra="forbid")

    required_obs_columns: list[str] = Field(default_factory=list)
    required_var_columns: list[str] = Field(default_factory=list)
    require_x: bool = True
    require_raw: bool = False
    unique_obs_names: bool = True
    unique_var_names: bool = True
    max_index_values: int = Field(default=1_000_000, ge=1)


class InputSpec(BaseModel):
    """One immutable input dataset."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=IDENTIFIER_PATTERN)
    path: str = Field(min_length=1)
    format: Literal["h5ad"] = "h5ad"
    checks: H5ADCheckSpec = Field(default_factory=H5ADCheckSpec)


class ArtifactSpec(BaseModel):
    """One expected output in the reproducibility evidence chain."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=IDENTIFIER_PATTERN)
    path: str = Field(min_length=1)
    kind: Literal["h5ad", "table", "figure", "report", "other"] = "other"


class StepSpec(BaseModel):
    """A declared analysis step; OmicsRepro never executes it."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=IDENTIFIER_PATTERN)
    script: str = Field(min_length=1)
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)


class Manifest(BaseModel):
    """Versioned v1 project contract."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    project: ProjectSpec
    inputs: list[InputSpec] = Field(min_length=1)
    artifacts: list[ArtifactSpec] = Field(default_factory=list)
    steps: list[StepSpec] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_graph(self) -> Manifest:
        """Reject ambiguous IDs and broken evidence-chain references."""

        collections = {
            "input": [item.id for item in self.inputs],
            "artifact": [item.id for item in self.artifacts],
            "step": [item.id for item in self.steps],
        }
        for label, identifiers in collections.items():
            duplicates = sorted({item for item in identifiers if identifiers.count(item) > 1})
            if duplicates:
                raise ValueError(f"duplicate {label} IDs: {', '.join(duplicates)}")

        input_ids = set(collections["input"])
        artifact_ids = set(collections["artifact"])
        valid_step_inputs = input_ids | artifact_ids
        for step in self.steps:
            unknown_inputs = sorted(set(step.inputs) - valid_step_inputs)
            unknown_outputs = sorted(set(step.outputs) - artifact_ids)
            if unknown_inputs:
                raise ValueError(
                    f"step {step.id!r} references unknown inputs: {', '.join(unknown_inputs)}"
                )
            if unknown_outputs:
                raise ValueError(
                    f"step {step.id!r} references unknown outputs: {', '.join(unknown_outputs)}"
                )
        return self


def discover_manifest(project: Path) -> Path:
    """Find exactly one supported manifest in a file or project directory."""

    candidate = project.expanduser()
    if candidate.is_file():
        if candidate.name not in MANIFEST_NAMES:
            raise ManifestError(
                f"manifest must be named {MANIFEST_NAMES[0]} or {MANIFEST_NAMES[1]}"
            )
        return candidate.resolve()
    if not candidate.is_dir():
        raise ManifestError(f"project path does not exist or is not a directory: {candidate}")

    matches = [candidate / name for name in MANIFEST_NAMES if (candidate / name).is_file()]
    if not matches:
        raise ManifestError(f"no {MANIFEST_NAMES[0]} found under {candidate.resolve()}")
    if len(matches) > 1:
        raise ManifestError(f"multiple manifests found under {candidate.resolve()}")
    return matches[0].resolve()


def load_manifest(path: Path) -> Manifest:
    """Load YAML using safe parsing and validate it against schema version 1."""

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ManifestError(f"could not read manifest {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ManifestError(f"manifest {path} must contain a YAML mapping")
    try:
        return Manifest.model_validate(raw)
    except ValidationError as exc:
        raise ManifestError(f"invalid manifest {path}:\n{exc}") from exc
