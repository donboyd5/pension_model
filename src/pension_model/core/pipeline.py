"""
End-to-end pension model pipeline.

Flows from raw inputs through benefit table construction to liability output.
Each step is validated against R intermediate data.

Pipeline:
  1. Load raw inputs (salary, headcount, decrement tables, mortality, constants)
  2. Build salary_headcount_table → salary_benefit_table
  3. Build separation_rate_table
  4. Build ann_factor_table → benefit_table → final_benefit_table
  5. Build benefit_val_table (PVFB, PVFS, NC)
  6. Join with workforce projections → liability components
  7. Aggregate by year → total AAL
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

from pension_model.config_schema import PlanConfig
from pension_model.core.benefit_tables import (
    build_salary_headcount_table,
    build_entrant_profile,
    build_salary_benefit_table,
    build_separation_rate_table,
    build_benefit_table,
    build_final_benefit_table,
    build_benefit_val_table,
)
from pension_model.core.pipeline_current import (
    _get_pmt,
    compute_current_retiree_liability,
    compute_current_term_vested_liability,
)
from pension_model.core.pipeline_projected import (
    compute_active_liability,
    compute_refund_liability,
    compute_retire_liability,
    compute_term_liability,
)


def compute_adjustment_ratio(class_or_inputs, headcount: pd.DataFrame | None = None,
                             constants: PlanConfig | None = None) -> float:
    """Return a class headcount adjustment ratio.

    Preferred path: pass a class input dict prepared by ``load_plan_inputs``,
    which includes the precomputed ``_adjustment_ratio``.

    Backward-compatible path: pass ``(class_name, headcount_df, constants)``.
    This retains the stage-3 long-format fix for tests and debugging without
    re-introducing file I/O into the core pipeline.
    """
    if isinstance(class_or_inputs, dict):
        return float(class_or_inputs["_adjustment_ratio"])

    if headcount is None or constants is None:
        raise TypeError(
            "compute_adjustment_ratio() expects either an inputs dict or "
            "(class_name, headcount_df, constants)"
        )

    if "count" in headcount.columns:
        raw_total = float(headcount["count"].sum())
    else:
        raw_total = float(headcount.iloc[:, 1:].sum().sum())
    return constants.class_data[class_or_inputs].total_active_member / raw_total


def _compute_cb_icr_series(inputs: dict, constants: PlanConfig) -> tuple[float, pd.Series]:
    """Build expected and actual ICR series for cash-balance plans."""
    from pension_model.core.icr import compute_actual_icr_series, compute_expected_icr

    cash_balance = constants.cash_balance
    expected_icr = compute_expected_icr(
        constants.model_return,
        cash_balance.get("return_volatility", 0.12),
        cash_balance["icr_smooth_period"],
        cash_balance["icr_floor"],
        cash_balance["icr_cap"],
        cash_balance["icr_upside_share"],
    )
    years = range(constants.min_entry_year, constants.max_year + 1)
    ret_scenario = inputs.get("_return_scenario")
    if ret_scenario is None:
        ret_scenario = pd.Series(constants.model_return, index=list(years))
    actual_icr_series = compute_actual_icr_series(
        years,
        constants.start_year,
        ret_scenario,
        cash_balance["icr_smooth_period"],
        cash_balance["icr_floor"],
        cash_balance["icr_cap"],
        cash_balance["icr_upside_share"],
    )
    return expected_icr, actual_icr_series


def _build_class_benefit_prelude(
    class_name: str,
    inputs: dict,
    constants: PlanConfig,
    *,
    has_cb: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, float | None]:
    """Build the per-class tables needed before stacked plan-wide builders."""
    adjustment_ratio = compute_adjustment_ratio(inputs)

    expected_icr = None
    actual_icr_series = None
    if has_cb:
        expected_icr, actual_icr_series = _compute_cb_icr_series(inputs, constants)

    salary_headcount = build_salary_headcount_table(
        inputs["salary"],
        inputs["headcount"],
        inputs["salary_growth"],
        class_name,
        adjustment_ratio,
        constants.ranges.start_year,
        constants=constants,
    )

    entrant_profile = (
        inputs["_entrant_profile"].copy()
        if "_entrant_profile" in inputs
        else build_entrant_profile(salary_headcount)
    )
    entrant_profile_tagged = entrant_profile.copy()
    entrant_profile_tagged["class_name"] = class_name

    salary_benefit = build_salary_benefit_table(
        salary_headcount,
        entrant_profile,
        inputs["salary_growth"],
        class_name,
        constants,
        actual_icr_series=actual_icr_series,
        forward_salary_growth=inputs.get("forward_salary_growth"),
    )

    if "_separation_rate" in inputs:
        separation_rate = inputs["_separation_rate"]
    else:
        separation_rate = build_separation_rate_table(
            inputs["term_rate_avg"],
            inputs["normal_retire_tier1"],
            inputs["normal_retire_tier2"],
            inputs["early_retire_tier1"],
            inputs["early_retire_tier2"],
            entrant_profile,
            class_name,
            constants,
        )

    return (
        salary_headcount,
        entrant_profile_tagged,
        salary_benefit,
        separation_rate,
        expected_icr,
    )


def _cast_class_name_categories(frames: list[pd.DataFrame], classes: list[str]) -> None:
    """Convert class_name to a shared categorical dtype in place."""
    class_cat = pd.CategoricalDtype(categories=list(classes))
    for frame in frames:
        frame["class_name"] = frame["class_name"].astype(class_cat)



def build_plan_benefit_tables(
    inputs_by_class: dict,
    constants: PlanConfig,
) -> dict:
    """Build every benefit table the plan needs in a single stacked pass.

    Replaces the per-class build_benefit_tables that was called in a 7x
    loop. All heavy work (ann_factor / benefit / final_benefit /
    benefit_val) is executed once across all classes via the
    stacked-capable builders, amortizing fixed pandas overhead and
    enabling natural cross-class deduplication.

    The per-class prelude (salary_headcount, entrant_profile,
    salary_benefit, separation_rate) still runs in a loop because each
    class's inputs are inherently per-class DataFrames, but the
    individual builders are fast and the outputs are stacked
    immediately via pd.concat.

    Each class owns its own decrement files, so separation_rate is built
    once per class (no sep_class indirection).

    Args:
        inputs_by_class: dict {class_name: inputs dict from load_plan_data}.
        constants: PlanConfig.
    Returns:
        Dict of stacked DataFrames keyed by:
          salary_headcount, entrant_profile, salary_benefit,
          separation_rate, ann_factor, benefit, final_benefit, benefit_val.
        Every frame carries class_name.
    """
    from pension_model.core.benefit_tables import build_ann_factor_table

    classes = list(constants.classes)

    # Plan-wide CB flag — if any class in the plan uses CB, we compute ICR.
    has_cb = "cb" in constants.benefit_types and constants.cash_balance is not None

    cm_by_class = {cn: inputs_by_class[cn]["_compact_mortality"] for cn in classes}
    expected_icr_by_class: dict = {}

    sh_frames: list = []
    ep_frames: list = []
    sbt_frames: list = []
    sep_frames: list = []

    for cn in classes:
        sh, ep_tagged, sbt, sep, expected_icr = _build_class_benefit_prelude(
            cn,
            inputs_by_class[cn],
            constants,
            has_cb=has_cb,
        )
        if expected_icr is not None:
            expected_icr_by_class[cn] = expected_icr

        sh_frames.append(sh)
        ep_frames.append(ep_tagged)
        sbt_frames.append(sbt)
        sep_frames.append(sep)

    salary_headcount = pd.concat(sh_frames, ignore_index=True)
    entrant_profile = pd.concat(ep_frames, ignore_index=True)
    salary_benefit = pd.concat(sbt_frames, ignore_index=True)
    separation_rate = pd.concat(sep_frames, ignore_index=True)

    # Convert class_name to pandas Categorical across every plan-wide frame.
    # Downstream pandas groupby / merge / sort operations hash and compare
    # categorical int codes rather than Python str objects, which is
    # materially faster on the large stacked frames.
    _cast_class_name_categories(
        [salary_headcount, entrant_profile, salary_benefit, separation_rate],
        classes,
    )

    # --- Stacked builders: one call each, spanning every class at once ---
    ann_factor = build_ann_factor_table(
        salary_benefit_table=salary_benefit,
        compact_mortality_by_class=cm_by_class,
        constants=constants,
        expected_icr_by_class=expected_icr_by_class or None,
    )
    benefit = build_benefit_table(ann_factor, salary_benefit, constants)
    final_benefit = build_final_benefit_table(
        benefit, use_earliest_retire=constants.use_earliest_retire,
    )

    # build_benefit_val_table takes a scalar expected_icr. Multi-class CB
    # is not currently supported; when the plan has exactly one CB class,
    # pass its ICR. For plans without CB, None.
    if expected_icr_by_class:
        scalar_icr = next(iter(expected_icr_by_class.values()))
    else:
        scalar_icr = None
    benefit_val = build_benefit_val_table(
        salary_benefit, final_benefit, separation_rate, constants,
        expected_icr=scalar_icr, ann_factor_table=ann_factor,
    )

    return {
        "salary_headcount": salary_headcount,
        "entrant_profile": entrant_profile,
        "salary_benefit": salary_benefit,
        "separation_rate": separation_rate,
        "ann_factor": ann_factor,
        "benefit": benefit,
        "final_benefit": final_benefit,
        "benefit_val": benefit_val,
    }


def _sum_cols(df, pattern_parts, default=0.0):
    """Sum all columns matching f"aal_{component}_{bt}_{period}_est" patterns."""
    total = default
    for col in df.columns:
        for part in pattern_parts:
            if part in col:
                total = total + df[col]
                break
    return total


def _compute_aal_totals(result):
    """Compute aal_legacy_est, aal_new_est, total_aal_est, tot_ben_refund from
    whatever benefit-type columns are present. Works for any combination of DB/CB/DC."""
    # Legacy AAL = sum of aal_active_{bt}_legacy + aal_term_{bt}_legacy + aal_retire_{bt}_legacy
    #              + retire_current + term_current
    legacy_aal = 0.0
    new_aal = 0.0
    legacy_ben = 0.0
    new_ben = 0.0

    for col in result.columns:
        if col.startswith("aal_active_") and col.endswith("_legacy_est"):
            legacy_aal = legacy_aal + result[col]
        elif col.startswith("aal_active_") and col.endswith("_new_est"):
            new_aal = new_aal + result[col]
        elif col.startswith("aal_term_") and col.endswith("_legacy_est") and "current" not in col:
            legacy_aal = legacy_aal + result[col]
        elif col.startswith("aal_term_") and col.endswith("_new_est") and "current" not in col:
            new_aal = new_aal + result[col]
        elif col.startswith("aal_retire_") and col.endswith("_legacy_est") and "current" not in col:
            legacy_aal = legacy_aal + result[col]
        elif col.startswith("aal_retire_") and col.endswith("_new_est") and "current" not in col:
            new_aal = new_aal + result[col]
        elif col.startswith("refund_") and col.endswith("_legacy_est"):
            legacy_ben = legacy_ben + result[col]
        elif col.startswith("refund_") and col.endswith("_new_est"):
            new_ben = new_ben + result[col]
        elif col.startswith("retire_ben_") and col.endswith("_legacy_est") and "current" not in col:
            legacy_ben = legacy_ben + result[col]
        elif col.startswith("retire_ben_") and col.endswith("_new_est") and "current" not in col:
            new_ben = new_ben + result[col]

    # Current retiree and term vested (not benefit-type-specific)
    if "aal_retire_current_est" in result.columns:
        legacy_aal = legacy_aal + result["aal_retire_current_est"]
    if "aal_term_current_est" in result.columns:
        legacy_aal = legacy_aal + result["aal_term_current_est"]
    if "retire_ben_current_est" in result.columns:
        legacy_ben = legacy_ben + result["retire_ben_current_est"]
    if "retire_ben_term_est" in result.columns:
        legacy_ben = legacy_ben + result["retire_ben_term_est"]

    result["aal_legacy_est"] = legacy_aal
    result["aal_new_est"] = new_aal
    result["total_aal_est"] = legacy_aal + new_aal
    result["tot_ben_refund_legacy_est"] = legacy_ben
    result["tot_ben_refund_new_est"] = new_ben
    result["tot_ben_refund_est"] = legacy_ben + new_ben
    result["liability_gain_loss_legacy_est"] = 0.0
    result["liability_gain_loss_new_est"] = 0.0
    result["total_liability_gain_loss_est"] = 0.0


def _project_and_aggregate_class(
    class_name: str,
    class_tables: dict,
    class_inputs: dict,
    constants,
    *,
    no_new_entrants: bool = False,
    on_stage=None,
) -> pd.DataFrame:
    """Per-class workforce projection + liability aggregation.

    Takes pre-built benefit tables (already sliced to this class from the
    plan-wide stacked frames) plus the class's raw inputs (needed for
    CompactMortality and current-retiree projection), and returns the
    class liability DataFrame. Internal helper — callers go through
    run_plan_pipeline.
    """
    from pension_model.core.workforce import project_workforce

    from pension_model.core.benefit_tables import _resolve_sep_type_vec

    bvt = class_tables["benefit_val"]
    fbt = class_tables["final_benefit"]
    bvt_bd = bvt[["entry_year", "entry_age", "yos", "term_age",
                  "ret_status"]].copy()
    bvt_bd["sep_type"] = _resolve_sep_type_vec(bvt_bd["ret_status"].values)
    bvt_bd["ben_decision"] = bvt_bd["sep_type"].map(
        {"retire": "retire", "vested": "mix", "non_vested": "refund"})
    bvt_bd.loc[bvt_bd["yos"] == 0, "ben_decision"] = np.nan
    ben_decisions = bvt_bd.merge(
        fbt[["entry_year", "entry_age", "term_age", "dist_age"]].drop_duplicates(),
        on=["entry_year", "entry_age", "term_age"], how="left",
    )
    ben_decisions["dist_age"] = ben_decisions["dist_age"].fillna(
        ben_decisions["term_age"]).astype(int)
    ben_decisions = ben_decisions[ben_decisions["ben_decision"].notna()]

    # Initial active population from this class's salary_headcount
    sh = class_tables["salary_headcount"]
    valid_entry_ages = set(class_tables["entrant_profile"]["entry_age"].values)
    initial_active = sh[sh["entry_age"].isin(valid_entry_ages)][
        ["entry_age", "age", "count"]].rename(columns={"count": "n_active"}).copy()
    initial_active = initial_active[initial_active["n_active"] > 0]

    if on_stage:
        on_stage("workforce")
    cm = class_inputs["_compact_mortality"]
    wf = project_workforce(
        initial_active, class_tables["separation_rate"], ben_decisions, cm,
        class_tables["entrant_profile"], class_name,
        constants.ranges.start_year, constants.ranges.model_period,
        constants.economic.pop_growth, constants.benefit.retire_refund_ratio,
        no_new_entrants=no_new_entrants,
        constants=constants,
    )

    if on_stage:
        on_stage("liability")
    active = compute_active_liability(
        wf["wf_active"], class_tables["benefit_val"], class_name, constants)
    term = compute_term_liability(
        wf["wf_term"], class_tables["benefit_val"], class_tables["benefit"],
        class_name, constants)
    refund = compute_refund_liability(
        wf["wf_refund"], class_tables["benefit"], class_name, constants)
    retire = compute_retire_liability(
        wf["wf_retire"], class_tables["benefit"], class_tables["ann_factor"],
        class_name, constants)

    cd = constants.class_data[class_name]
    ben_payment = cd.ben_payment
    retire_current = compute_current_retiree_liability(
        class_inputs["ann_factor_retire"], class_inputs["retiree_distribution"],
        cd.retiree_pop, ben_payment, constants)
    term_current = compute_current_term_vested_liability(class_name, constants)

    years = pd.DataFrame({"year": range(
        constants.ranges.start_year,
        constants.ranges.start_year + constants.ranges.model_period + 1,
    )})
    result = years.merge(active, on="year", how="left")
    result = result.merge(term, on="year", how="left")
    result = result.merge(refund, on="year", how="left")
    result = result.merge(retire, on="year", how="left")
    result = result.merge(retire_current, on="year", how="left")
    result = result.merge(term_current, on="year", how="left")
    result = result.fillna(0)
    _compute_aal_totals(result)
    return result


def _split_plan_tables_by_class(plan_tables: dict, classes: list) -> dict:
    """Split plan-wide stacked tables into per-class views in one pass each.

    Returns {class_name: {table_name: DataFrame}}.

    Uses dict(tuple(df.groupby("class_name"))) which does a single O(n) pass
    per frame instead of N full-frame boolean-index scans. Every frame,
    including separation_rate, is keyed by class_name — there is no
    sep_class indirection.

    The class_name column is stripped from the sliced frames; inside the
    per-class projection step it is redundant (every row has the same
    value) and it measurably slows downstream .iterrows() calls in
    project_workforce.
    """
    by_table_then_class: dict = {}
    for name, df in plan_tables.items():
        if "class_name" in df.columns:
            groups = dict(tuple(df.groupby("class_name", sort=False)))
            by_table_then_class[name] = {
                cn: g.drop(columns=["class_name"]).reset_index(drop=True)
                for cn, g in groups.items()
            }
        else:
            by_table_then_class[name] = {cn: df for cn in classes}

    result: dict = {}
    for cn in classes:
        result[cn] = {name: slices.get(cn)
                      for name, slices in by_table_then_class.items()}
    return result


def run_plan_pipeline(
    constants: PlanConfig,
    baseline_dir: Path = None,
    *,
    no_new_entrants: bool = False,
    on_stage=None,
    progress: bool = False,
) -> dict:
    """End-to-end pipeline for an entire plan: stage 3 data → per-class liability.

    Loads inputs once per class, builds every benefit table in a single
    plan-wide stacked call via build_plan_benefit_tables, then loops the
    classes to project workforce and aggregate liabilities (which
    currently still run per-class because project_workforce uses numpy
    matrices sized per class).

    Args:
        constants: PlanConfig.
        baseline_dir: Deprecated, ignored. Kept for caller compatibility.
        no_new_entrants: Rundown mode — no new hires projected.
        on_stage: Optional callback(stage_name: str) for progress reporting.
        progress: If True, print percent-done progress to stdout.

    Returns:
        Dict {class_name: liability DataFrame} — one entry per class in
        constants.classes, matching the old run_class_pipeline_e2e output
        shape per class.
    """
    from pension_model.core.data_loader import load_plan_inputs

    classes = list(constants.classes)

    # Load raw inputs for all classes; attaches reduction tables to config
    constants, inputs_by_class = load_plan_inputs(constants)

    if on_stage:
        on_stage("benefit_tables")
    plan_tables = build_plan_benefit_tables(inputs_by_class, constants)

    # Split stacked tables into per-class views once (single groupby pass
    # per frame) instead of re-scanning inside the per-class loop.
    class_tables_by_name = _split_plan_tables_by_class(plan_tables, classes)

    liability = {}
    n = len(classes)
    for i, cn in enumerate(classes):
        if progress:
            pct = int(i / n * 100)
            sys.stdout.write(f"\r    {pct:3d}%")
            sys.stdout.flush()
        liability[cn] = _project_and_aggregate_class(
            cn, class_tables_by_name[cn], inputs_by_class[cn], constants,
            no_new_entrants=no_new_entrants, on_stage=on_stage,
        )
    if progress:
        sys.stdout.write(f"\r    100% done\n")
        sys.stdout.flush()

    return liability
