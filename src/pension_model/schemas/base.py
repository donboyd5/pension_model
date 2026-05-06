"""Shared base for plan_config schema models."""

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """Base for plan_config schema models.

    ``extra="forbid"`` rejects unknown fields at parse time — the
    typo-detection guarantee that motivated the migration. ``frozen``
    matches the project-wide "configs are immutable" rule and lets
    models be hashed/compared safely.

    Type-coercion strictness is left at pydantic v2's default. JSON
    integers are accepted for float fields (Python's number tower
    treats int as a subset of float), which matches how plan_config
    values are written today.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )
