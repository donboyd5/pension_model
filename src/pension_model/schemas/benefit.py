"""Schema for the ``benefit`` block of plan_config.json."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from pension_model.schemas.base import StrictModel


class Cola(StrictModel):
    """Cost-of-living adjustment assumptions.

    Has two layers of fields:

    * **Typed fixed fields** for retiree-side and proration:
      ``current_retire``, ``current_retire_one_time``, ``one_time_cola``,
      ``proration_cutoff_year``.

    * **Dynamic per-tier active rates** (e.g. ``tier_1_active``,
      ``tier_2_active_constant``) — admitted via ``extra="allow"``
      because the keys depend on the plan's tier names. Read these
      via ``getattr(cola, key, default)`` from caller code.

    A future cleanup PR may move per-tier rates into a typed sub-dict
    so the whole model can be strict; for now the loose form
    preserves the existing JSON shape.
    """

    # The override loosens StrictModel's extra="forbid" to admit
    # tier-keyed extras. Strict on type coercion still applies to
    # the typed fields below.
    model_config = ConfigDict(extra="allow", frozen=True)

    current_retire: float = 0.0
    current_retire_one_time: float = 0.0
    one_time_cola: bool = False
    proration_cutoff_year: int | None = None


class CashBalance(StrictModel):
    """Cash-balance plan parameters (TXTRS-style)."""

    ee_pay_credit: float
    er_pay_credit: float
    vesting_yos: int
    icr_smooth_period: int
    icr_floor: float
    icr_cap: float
    icr_upside_share: float
    annuity_conversion_rate: float
    return_volatility: float = 0.12


class DcSpec(StrictModel):
    """Defined-contribution sub-block (TXTRS-style)."""

    ee_cont_rate: float
    assumed_return: float
    return_volatility: float = 0.12


class Benefit(StrictModel):
    """Plan-level benefit assumptions.

    ``cal_factor`` and ``min_benefit_monthly`` are admitted but are
    not yet used by every plan — the loader injects ``cal_factor``
    from ``calibration.json`` if the plan has one, and
    ``min_benefit_monthly`` is a TXTRS-only feature today.
    """

    db_ee_cont_rate: float
    db_ee_interest_rate: float = 0.0
    retire_refund_ratio: float = 1.0
    fas_years_default: int
    fas_years_grandfathered: int | None = Field(
        default=None,
        description="Override fas_years for grandfathered tiers (TXTRS).",
    )
    min_benefit_monthly: float | None = Field(
        default=None,
        description="Floor on monthly benefit at retirement (TXTRS).",
    )
    cal_factor: float = Field(
        default=1.0,
        description="Plan-wide calibration scalar applied to DB benefits. "
        "Injected by the loader from calibration.json when present.",
    )
    benefit_types: list[str] = Field(default_factory=lambda: ["db"])
    cola: Cola = Field(default_factory=Cola)
    cash_balance: CashBalance | None = None
    dc: DcSpec | None = None
