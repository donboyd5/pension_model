"""Schema for the ``economic`` block of plan_config.json."""

from __future__ import annotations

from pydantic import Field, model_validator

from pension_model.schemas.base import StrictModel


class Economic(StrictModel):
    """Plan-level economic assumptions.

    Source-of-truth for discount rates, payroll/population growth,
    and the asset-return scenario reference. ``baseline_*`` fields
    are populated by the loader from the pre-scenario raw config so
    that scenario overrides don't disturb the term-vested cashflow
    scaling — see ``docs/design/discount_rate_scenarios.md``.
    """

    dr_current: float = Field(description="Current discount rate.")
    dr_new: float = Field(description="Discount rate for new hires.")
    dr_old: float | None = Field(
        default=None,
        description="Legacy discount rate (used in some amortization "
        "calcs). Defaults to dr_current.",
    )
    payroll_growth: float
    pop_growth: float = 0.0
    model_return: float | None = Field(
        default=None,
        description="Asset return assumption for the funding model. " "Defaults to dr_current.",
    )
    asset_return_path: dict | None = None

    # Snapshots from before any scenario override. Not parsed from
    # raw["economic"]; populated by the loader.
    baseline_dr_current: float
    baseline_model_return: float

    @model_validator(mode="after")
    def _apply_dr_defaults(self) -> Economic:
        # Frozen models need object.__setattr__ for back-fills.
        if self.dr_old is None:
            object.__setattr__(self, "dr_old", self.dr_current)
        if self.model_return is None:
            object.__setattr__(self, "model_return", self.dr_current)
        return self
