"""Schema for the ``valuation_inputs`` block of plan_config.json,
plus the merged ``class_data`` view used at runtime."""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from pension_model.schemas.base import StrictModel


class ValuationInputs(StrictModel):
    """One class's actuarial-valuation snapshot.

    Used to seed initial AAL / payroll / member counts and
    benefit-payment streams. Each plan declares one entry per class
    under ``valuation_inputs`` in plan_config.json.
    """

    ben_payment: float = Field(
        description="Initial-year pension benefit payments to current "
        "retirees. Seeds the retiree liability projection.",
    )
    retiree_pop: int
    total_active_member: int
    er_dc_cont_rate: float = Field(
        default=0.0,
        description="Employer DC contribution rate (used when "
        "benefit_types includes 'dc').",
    )
    val_norm_cost: float
    val_aal: Optional[float] = Field(
        default=None,
        description="AV-published actuarial accrued liability (used "
        "for component-by-component calibration; optional).",
    )
    val_payroll: Optional[float] = Field(
        default=None,
        description="AV-published payroll for this class (FRS-only "
        "today).",
    )
    headcount_group: Optional[list[str]] = Field(
        default=None,
        description="Classes whose headcount totals must agree (FRS "
        "uses this to enforce eco/eso/judges share total_active_member).",
    )


class ClassData(StrictModel):
    """Per-class merged view of valuation_inputs + calibration.

    Replaces the ``SimpleNamespace`` from
    ``config_compat.build_class_data_namespace``. Same access pattern
    (e.g. ``config.class_data[cn].nc_cal``) but type-checked.
    """

    ben_payment: float
    retiree_pop: int
    total_active_member: int
    er_dc_cont_rate: float
    val_norm_cost: float
    nc_cal: float = 1.0
    pvfb_term_current: float = 0.0
