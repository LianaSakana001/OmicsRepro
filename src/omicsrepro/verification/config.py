"""Configuration for experimental scientific verification contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class VerificationContractError(ValueError):
    """Raised when a verification contract cannot be read or validated."""


class PopulationSpec(BaseModel):
    """Population selected for the declared comparison."""

    model_config = ConfigDict(extra="forbid")

    value: str = Field(min_length=1)
    column: str | None = Field(default=None, min_length=1)


class ConditionSpec(BaseModel):
    """Declared comparison and its metadata column."""

    model_config = ConfigDict(extra="forbid")

    column: str = Field(min_length=1)
    case: str = Field(min_length=1)
    control: str = Field(min_length=1)

    @model_validator(mode="after")
    def distinct_groups(self) -> ConditionSpec:
        """A contrast cannot compare a label with itself."""

        if self.case == self.control:
            raise ValueError("case and control labels must differ")
        return self


class ReplicateSpec(BaseModel):
    """Biological replication required by the contract."""

    model_config = ConfigDict(extra="forbid")

    concept: Literal["donor"] = "donor"
    min_per_group: int = Field(default=2, ge=1)


class ScrnaDEContractSpec(BaseModel):
    """Experimental v0 preflight contract for between-condition scRNA-seq DE."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    contract: Literal["scrna.de_between_conditions/v0"]
    input_id: str = Field(min_length=1)
    population: PopulationSpec
    condition: ConditionSpec
    replicate: ReplicateSpec = Field(default_factory=ReplicateSpec)
    max_observations: int = Field(default=2_000_000, ge=1)
    max_categories: int = Field(default=100_000, ge=1)
    max_entities: int = Field(default=100_000, ge=1)


def load_verification_contract(path: Path) -> ScrnaDEContractSpec:
    """Load one fail-closed experimental contract from YAML."""

    try:
        raw = yaml.safe_load(path.expanduser().read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        message = f"could not read verification contract {path}: {exc}"
        raise VerificationContractError(message) from exc
    if not isinstance(raw, dict):
        raise VerificationContractError("verification contract must contain a YAML mapping")
    try:
        return ScrnaDEContractSpec.model_validate(raw)
    except ValidationError as exc:
        raise VerificationContractError(f"invalid verification contract {path}:\n{exc}") from exc
