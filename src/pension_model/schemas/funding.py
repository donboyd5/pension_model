"""Schema for the ``funding`` block of plan_config.json."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from pension_model.schemas.base import StrictModel

# ---------------------------------------------------------------------------
# AVA smoothing — method-discriminated union
# ---------------------------------------------------------------------------


class CorridorAvaSmoothing(StrictModel):
    """Corridor smoothing parameters.

    Each year, smooths AVA toward MVA by ``recognition_fraction`` of
    the gap, bounded to ``[corridor_low * mva, corridor_high * mva]``.
    """

    method: Literal["corridor"]
    corridor_low: float = 0.8
    corridor_high: float = 1.2
    recognition_fraction: float = 0.2


class GainLossAvaSmoothing(StrictModel):
    """Gain/loss deferral cascade parameters.

    Each year's asset gain/loss is deferred and recognized over
    ``recognition_period`` years.
    """

    method: Literal["gain_loss"]
    recognition_period: int


# Discriminated union by ``method``. Pydantic dispatches to the right
# concrete model based on the method tag.
AvaSmoothing = Annotated[
    CorridorAvaSmoothing | GainLossAvaSmoothing,
    Field(discriminator="method"),
]


# ---------------------------------------------------------------------------
# Statutory rate components
# ---------------------------------------------------------------------------


class RateScheduleEntry(StrictModel):
    """One step in a year-keyed step-function rate schedule."""

    from_year: int
    rate: float


class RampSpec(StrictModel):
    """Linear ramp parameters for an employer-rate component."""

    rate_per_year: float
    end_year: int


class RateComponentSpec(StrictModel):
    """One term in the statutory employer-rate cascade.

    Each component contributes ``rate(year) * payroll_share`` to the
    effective employer rate. Rate is specified as either a step
    schedule or a linear ramp — exactly one must be present.
    """

    name: str
    payroll_share: float = 1.0
    schedule: list[RateScheduleEntry] | None = None
    initial_rate: float | None = None
    ramp: RampSpec | None = None
    start_year: int | None = None

    @model_validator(mode="after")
    def _check_rate_form(self) -> RateComponentSpec:
        has_schedule = self.schedule is not None
        has_ramp = self.ramp is not None
        if not has_schedule and not has_ramp:
            raise ValueError(
                f"RateComponentSpec {self.name!r}: must specify either "
                f"'schedule' (step function) or 'ramp' (with "
                f"'initial_rate'). Neither was provided."
            )
        if has_schedule and has_ramp:
            raise ValueError(
                f"RateComponentSpec {self.name!r}: 'schedule' and 'ramp' "
                f"are mutually exclusive. Pick one."
            )
        return self


class StatutoryRates(StrictModel):
    """Statutory contribution-rate definitions.

    Required when ``Funding.contribution_strategy == \"statutory\"``.
    """

    ee_rate_schedule: list[RateScheduleEntry]
    er_rate_components: list[RateComponentSpec]


# ---------------------------------------------------------------------------
# Funding legs
# ---------------------------------------------------------------------------


class LegDef(StrictModel):
    """One funding leg.

    Either or both of ``entry_year_min`` and ``entry_year_max`` may be
    omitted to mean open-ended. ``*_param`` strings of ``"new_year"``
    resolve to ``Ranges.new_year`` at access time (today the only
    supported parametric reference).
    """

    name: str
    entry_year_min: int | None = None
    entry_year_max: int | None = None
    entry_year_min_param: Literal["new_year"] | None = None
    entry_year_max_param: Literal["new_year"] | None = None


def _default_legs() -> list[LegDef]:
    """Default 2-leg layout (legacy/new) keyed off ``new_year``.

    Used when ``Funding.legs`` is omitted, preserving today's
    pre-explicit-legs behavior.
    """
    return [
        LegDef(name="legacy", entry_year_max_param="new_year"),
        LegDef(name="new", entry_year_min_param="new_year"),
    ]


# ---------------------------------------------------------------------------
# Top-level Funding model
# ---------------------------------------------------------------------------


class Funding(StrictModel):
    """Funding-model parameters."""

    contribution_strategy: Literal["statutory", "actuarial"]
    policy: str = Field(description="Funding policy. Today: 'statutory' or 'adc'.")
    amo_method: str
    amo_period_new: int
    amo_pay_growth: float
    funding_lag: int = 1

    amo_period_current: int | None = None
    amo_period_term: int = 50
    amo_term_growth: float = 0.03

    has_drop: bool = False
    drop_reference_class: str | None = None

    ava_smoothing: AvaSmoothing
    statutory_rates: StatutoryRates | None = None
    legs: list[LegDef] = Field(default_factory=_default_legs)

    @model_validator(mode="after")
    def _check_statutory_rates_present(self) -> Funding:
        if self.contribution_strategy == "statutory" and self.statutory_rates is None:
            raise ValueError(
                "funding.contribution_strategy is 'statutory' but "
                "funding.statutory_rates is missing. The statutory "
                "strategy requires a statutory_rates block declaring "
                "ee_rate_schedule and er_rate_components."
            )
        return self
