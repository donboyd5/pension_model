"""
Strategy classes for the funding model.

Two axes of variation between funding policies are *orthogonal* and
must be configurable independently:

  1. **Asset value smoothing.** How quickly investment gains/losses are
     recognized into the actuarial value of assets (AVA). Two methods
     are supported:

       * Five-year corridor (recognize 1/5 per year, bounded to a
         [80%, 120%] band around MVA). Operates at the *plan-aggregate*
         level, then allocates earnings back to classes proportionally.
       * Four-year gain/loss deferral cascade. Operates per-class.

  2. **Employer contribution policy.** How the year-loop computes the
     employer's normal cost and amortization payments:

       * Actuarial: pre-calibrated NC rates from the liability pipeline,
         amortization rate from the prior year's amort table payments.
       * Statutory: a base employer rate cascade
         (``base + surcharge * applicable_payroll_pct + extra``)
         drives the effective employer rate; under
         ``funding_policy = "statutory"`` the amortization rate is the
         residual of the statutory effective rate minus the employer
         normal cost rate.

The dispatch on ``len(constants.classes) == 1`` that lives in
``run_funding_model`` today bundles these two axes together — single-
class plans get gain/loss + statutory, multi-class plans get corridor
+ actuarial. The strategies in this module decouple them so a future
plan can mix and match (e.g. corridor + statutory) by changing config,
not code.

This module is *protocol scaffolding only*: the smoothing strategies
delegate verbatim to the existing helpers in ``_funding_helpers.py``;
the contribution strategy classes carry signatures and docstrings but
their method bodies are filled in by Step 10 of the unification
refactor (``Wire strategies into call sites``). Importing this module
introduces no numerical change to either funding path.
"""

from __future__ import annotations

from typing import ClassVar, Literal, Protocol, runtime_checkable

import pandas as pd

from pension_model.core._funding_helpers import (
    _ava_corridor_smoothing,
    _ava_gain_loss_smoothing,
)


# ---------------------------------------------------------------------------
# AVA smoothing strategies
# ---------------------------------------------------------------------------


@runtime_checkable
class AvaSmoothingStrategy(Protocol):
    """One year of asset value smoothing for a single asset leg.

    Smoothing operates per leg (e.g. ``legacy`` and ``new``) and the
    caller invokes the strategy once per leg. The leg name is *not*
    passed in — it lives at the call site, which is responsible for
    reading prior values and writing results onto the appropriate
    columns of the funding DataFrame.

    Implementations declare ``aggregation_level``:

      * ``"plan"``  — call once at the plan-aggregate level after every
        class has been processed for the year, then call
        ``allocate_to_classes`` to distribute earnings back to classes.
      * ``"class"`` — call once *per class* inside the class loop. The
        ``allocate_to_classes`` method is a no-op for these strategies.
    """

    aggregation_level: ClassVar[Literal["plan", "class"]]

    def smooth(
        self,
        ava_prev: float,
        net_cf: float,
        mva: float,
        dr: float,
        state: dict,
    ) -> dict:
        """Compute smoothed AVA values for one year and one asset leg.

        ``state`` carries strategy-specific extra inputs (e.g. prior
        deferral balances for gain/loss smoothing). Strategies that
        have no extra state ignore it.

        Returned dict shape is strategy-specific. The caller knows
        which strategy is in use and writes the keys it expects to
        the appropriate columns. (Step 11 will introduce a unified
        column-write helper that maps strategy result keys to
        DataFrame columns.)
        """
        ...

    def allocate_to_classes(
        self,
        agg: pd.DataFrame,
        funding: dict,
        class_names: list,
        i: int,
    ) -> None:
        """For plan-level smoothing, allocate aggregate AVA earnings
        back to individual classes proportionally to each class's
        ``ava_base``. For per-class smoothing, this is a no-op.
        """
        ...


class CorridorSmoothing:
    """Five-year corridor smoothing at the plan-aggregate level.

    Smooths each leg's AVA toward MVA at 1/5 per year, bounded to
    ``[0.8 * mva, 1.2 * mva]``. After smoothing the aggregate, allocates
    the realized earnings to each class in proportion to that class's
    pre-smoothing ``ava_base`` (= ``ava_prev + net_cf / 2``).
    """

    aggregation_level: ClassVar[Literal["plan", "class"]] = "plan"

    def smooth(
        self,
        ava_prev: float,
        net_cf: float,
        mva: float,
        dr: float,
        state: dict,  # noqa: ARG002 — corridor has no extra state
    ) -> dict:
        return _ava_corridor_smoothing(ava_prev, net_cf, mva, dr)

    def allocate_to_classes(
        self,
        agg: pd.DataFrame,
        funding: dict,
        class_names: list,
        i: int,
    ) -> None:
        """Distribute the aggregate's smoothed earnings to each class
        proportionally to that class's ``ava_base``.

        For each leg (``legacy`` and ``new``)::

            class_alloc = agg_alloc * class_ava_base / agg_ava_base
            class_unadj_ava = class_ava_prev + class_net_cf + class_alloc

        The ``ava_base != 0`` guard mirrors the original FRS code path
        (lines 488 and 492). The mid-year-cashflow base
        (``ava_prev + net_cf / 2``) was already written onto each
        class's frame inside the per-class loop, so this method only
        reads it.
        """
        for cn in class_names:
            f = funding[cn]
            if agg.loc[i, "ava_base_legacy"] != 0:
                f.loc[i, "alloc_inv_earnings_ava_legacy"] = (
                    agg.loc[i, "alloc_inv_earnings_ava_legacy"]
                    * f.loc[i, "ava_base_legacy"]
                    / agg.loc[i, "ava_base_legacy"]
                )
            f.loc[i, "unadj_ava_legacy"] = (
                f.loc[i - 1, "ava_legacy"]
                + f.loc[i, "net_cf_legacy"]
                + f.loc[i, "alloc_inv_earnings_ava_legacy"]
            )

            if agg.loc[i, "ava_base_new"] != 0:
                f.loc[i, "alloc_inv_earnings_ava_new"] = (
                    agg.loc[i, "alloc_inv_earnings_ava_new"]
                    * f.loc[i, "ava_base_new"]
                    / agg.loc[i, "ava_base_new"]
                )
            f.loc[i, "unadj_ava_new"] = (
                f.loc[i - 1, "ava_new"]
                + f.loc[i, "net_cf_new"]
                + f.loc[i, "alloc_inv_earnings_ava_new"]
            )
            funding[cn] = f


class GainLossSmoothing:
    """Four-year gain/loss deferral cascade at the per-class level.

    Each year's asset gain/loss is deferred and recognized in the
    following four years (``y4 → y3 → y2 → y1`` cascade with sign-
    aware offsetting). Operates per class; aggregate-level allocation
    is a no-op because each class has already smoothed its own assets.

    The ``state`` dict required by ``smooth`` must contain four keys:
    ``defer_y1_prev``, ``defer_y2_prev``, ``defer_y3_prev``,
    ``defer_y4_prev``.
    """

    aggregation_level: ClassVar[Literal["plan", "class"]] = "class"

    def smooth(
        self,
        ava_prev: float,
        net_cf: float,
        mva: float,
        dr: float,
        state: dict,
    ) -> dict:
        return _ava_gain_loss_smoothing(
            ava_prev,
            net_cf,
            mva,
            dr,
            state["defer_y1_prev"],
            state["defer_y2_prev"],
            state["defer_y3_prev"],
            state["defer_y4_prev"],
        )

    def allocate_to_classes(
        self,
        agg: pd.DataFrame,
        funding: dict,
        class_names: list,
        i: int,
    ) -> None:
        # No-op: each class is already smoothed inside the per-class loop.
        return None


# ---------------------------------------------------------------------------
# Employer contribution strategies
# ---------------------------------------------------------------------------


@runtime_checkable
class ContributionStrategy(Protocol):
    """Computes employer normal-cost and amortization rates / amounts
    for one class-year inside the funding loop.

    Implementations differ on:

      * Whether the employer normal-cost rate is the calibrated rate
        pre-populated from the liability pipeline (Actuarial), or the
        difference between a dynamically-computed total NC rate and an
        EE rate (Statutory).
      * Whether the amortization rate is a function of prior amort
        table payments (Actuarial), or the residual of an externally-
        set statutory effective rate (Statutory, when
        ``funding_policy == "statutory"``).
      * Whether a statutory rate cascade exists at all.

    Concrete impls fill in the body in Step 10 of the unification
    refactor; this Protocol is a documentation contract only.
    """

    def compute_year(
        self,
        f: pd.DataFrame,
        i: int,
        year: int,
        amo_state: dict,
    ) -> None:
        """Write contribution rate and amount columns to ``f.loc[i, :]``.

        ``amo_state`` carries any per-class amortization state the
        strategy needs (debt/pay/per arrays for the actuarial path).
        """
        ...


class ActuarialContributions:
    """Employer contributions driven by the actuarial pipeline.

    The employer normal-cost rate is read from the calibrated columns
    pre-populated by ``_populate_calibrated_nc_rates``; the
    amortization rate is computed from the prior year's amort table
    payments divided by payroll. There is no statutory rate cascade.

    Body filled in by Step 10.
    """

    def compute_year(
        self,
        f: pd.DataFrame,
        i: int,
        year: int,
        amo_state: dict,
    ) -> None:
        raise NotImplementedError(
            "ActuarialContributions.compute_year is filled in by Step 10."
        )


class StatutoryContributions:
    """Employer contributions driven by a statutory rate cascade.

    The employer effective rate is::

        er_stat_eff_rate = (
            er_stat_base_rate(year)
            + public_edu_surcharge_rate(year) * public_edu_payroll_pct
            + er_stat_extra_rate(year)
        )

    The term order is *load-bearing* (bit-identity risk #6 in the
    plan): floating-point addition is non-associative, and the
    original TRS code adds the surcharge term before the extra term.
    Implementations must preserve that order.

    Under ``funding_policy == "statutory"`` the amortization rate is
    the residual ``er_stat_eff_rate - er_nc_rate_*``; under any other
    funding policy the amortization rate falls back to the actuarial
    table calculation.

    Body filled in by Step 10.
    """

    def __init__(
        self,
        funding_policy: str,
        public_edu_payroll_pct: float,
        extra_er_stat_cont: float,
        extra_er_start_year: int,
        surcharge_ramp_end: int,
        surcharge_ramp_rate: float,
        er_base_schedule: list,
    ) -> None:
        self.funding_policy = funding_policy
        self.public_edu_payroll_pct = public_edu_payroll_pct
        self.extra_er_stat_cont = extra_er_stat_cont
        self.extra_er_start_year = extra_er_start_year
        self.surcharge_ramp_end = surcharge_ramp_end
        self.surcharge_ramp_rate = surcharge_ramp_rate
        self.er_base_schedule = er_base_schedule

    def compute_year(
        self,
        f: pd.DataFrame,
        i: int,
        year: int,
        amo_state: dict,
    ) -> None:
        raise NotImplementedError(
            "StatutoryContributions.compute_year is filled in by Step 10."
        )
