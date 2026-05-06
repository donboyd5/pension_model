"""Schema for ``calibration.json`` (top-level + per-class)."""

from __future__ import annotations

from typing import Optional

from pydantic import ConfigDict, Field

from pension_model.schemas.base import StrictModel


class ClassCalibration(StrictModel):
    """Per-class calibration values."""

    nc_cal: float = Field(
        default=1.0,
        description="Normal-cost calibration scalar. Multiplies the "
        "model's NC rate to match AV. Values near 1.0 mean the model "
        "is accurate for that class.",
    )
    pvfb_term_current: float = Field(
        default=0.0,
        description="PVFB on term-vested members at start year. "
        "Seeds the term-vested AAL where the AV doesn't break out a "
        "specific number.",
    )


class Calibration(StrictModel):
    """Top-level calibration.json structure.

    Free-text fields (``description``, ``source``, ``notes``) are
    documentation and don't drive logic. ``cal_factor`` is injected
    into ``Benefit.cal_factor`` by the loader. ``classes`` maps each
    class name to its per-class calibration block.
    """

    # Allow free-form documentation fields plus future per-class
    # entries the loader doesn't understand yet.
    model_config = ConfigDict(extra="allow", frozen=True)

    description: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    cal_factor: Optional[float] = None
    classes: dict[str, ClassCalibration] = Field(default_factory=dict)
