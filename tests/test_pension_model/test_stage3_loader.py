"""
Regression tests for the stage 3 data loader.

These tests exercise the stage 3 path explicitly — the pre-existing 230-test
FRS suite runs through `ModelConstants` + `_load_frs_inputs` (the Excel
loader) and never touches the stage 3 code, so bugs in the stage 3 path can
survive the existing suite.

History
-------
Bugs discovered on 2026-04-04:

1. `_build_mortality_from_csv` hardcoded the mortality table to "general"
   for every class, ignoring the per-class `base_table_map` in plan_config.
   Affected FRS special/admin (should use safety mortality).

2. `compute_adjustment_ratio` used `headcount.iloc[:, 1:].sum().sum()`,
   which assumes the legacy wide format (age + yos_2 + yos_7 + ...). Stage 3
   uses long format (age, yos, count), so the `yos` column was silently
   summed into the headcount denominator, deflating adj_ratio by ~0.3%.

3. Admin's DB-vs-DC design ratios were being taken from `class_groups`,
   which puts admin in `special_group` for tier eligibility. But R's
   liability model hardcodes `if (class_name == "special")` for design
   ratios, so admin actually gets regular-group ratios (0.75, 0.25, 0.25)
   in R. Config now has `design_ratio_group_map` to express this override.
   See GH issue #22 for a discussion of R's split grouping approach.

All three bugs were invisible to the existing 230-test FRS suite because
those tests use ModelConstants + _load_frs_inputs (the Excel loader) and
never touch the stage 3 code path.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

pytestmark = [
    pytest.mark.regression,
    pytest.mark.transitional,
    pytest.mark.plan_frs,
]

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

FRS_CLASSES = ["regular", "special", "admin", "eco", "eso",
               "judges", "senior_management"]
FRS_BASELINES = Path(__file__).parent.parent.parent / "plans" / "frs" / "baselines"


@pytest.fixture(scope="module")
def frs_config():
    from pension_model.plan_config import load_plan_config_by_name
    return load_plan_config_by_name("frs")


@pytest.fixture(scope="module")
def raw_dir():
    return Path(__file__).parent.parent.parent / "R_model" / "R_model_frs"


@pytest.mark.parametrize("class_name", FRS_CLASSES)
def test_stage3_mortality_matches_excel(class_name, frs_config, raw_dir):
    """Stage 3 CSV mortality must match the Excel-built mortality for every
    FRS class, across a wide range of ages and years, for both active and
    retiree rates.

    Guards against the base_table_map lookup bug: if _build_mortality_from_csv
    ever regresses to hardcoding a single table, special/admin will diverge.
    """
    from pension_model.core.data_loader import _build_mortality_from_csv
    from pension_model.core.mortality_builder import build_compact_mortality_from_excel

    mort_dir = Path(__file__).parent.parent.parent / "plans" / "frs" / "data" / "mortality"
    pub2010 = raw_dir / "pub-2010-headcount-mort-rates.xlsx"
    mp2018 = raw_dir / "mortality-improvement-scale-mp-2018-rates.xlsx"

    if not pub2010.exists() or not mort_dir.exists():
        pytest.skip("R_model Excel inputs or stage 3 mortality CSVs not available")

    cm_csv = _build_mortality_from_csv(frs_config, mort_dir, class_name)
    cm_xlsx = build_compact_mortality_from_excel(
        pub2010, mp2018, class_name, constants=frs_config
    )

    max_diff = 0.0
    for age in range(18, 121):
        for year in (2022, 2030, 2050, 2080):
            for is_retiree in (True, False):
                d = abs(
                    cm_csv.get_rate(age, year, is_retiree)
                    - cm_xlsx.get_rate(age, year, is_retiree)
                )
                if d > max_diff:
                    max_diff = d

    assert max_diff < 1e-12, (
        f"{class_name}: stage 3 mortality differs from Excel by {max_diff:.2e} "
        f"(expected zero). Check _build_mortality_from_csv uses base_table_map."
    )


@pytest.mark.parametrize("class_name", ["special", "admin"])
def test_stage3_mortality_uses_safety_table(class_name, frs_config):
    """Explicit check that the per-class base_table_map is being honored for
    FRS classes that should use the safety mortality table.

    At age 30, safety mortality is materially different from general, so a
    wrong-table bug would show up here as a clearly non-zero diff.
    """
    from pension_model.core.data_loader import _build_mortality_from_csv
    from pension_model.core.mortality_builder import build_compact_mortality_from_csv

    mort_dir = Path(__file__).parent.parent.parent / "plans" / "frs" / "data" / "mortality"
    if not mort_dir.exists():
        pytest.skip("Stage 3 mortality CSVs not available")

    cm_via_loader = _build_mortality_from_csv(frs_config, mort_dir, class_name)
    cm_safety = build_compact_mortality_from_csv(
        mort_dir / "base_rates.csv",
        mort_dir / "improvement_scale.csv",
        class_name,
        table_name="safety",
        min_age=frs_config.ranges.min_age,
        max_age=frs_config.ranges.max_age,
        max_year=(frs_config.ranges.start_year + frs_config.ranges.model_period
                  + frs_config.ranges.max_age - frs_config.ranges.min_age),
        constants=frs_config,
        male_mp_forward_shift=0,
    )

    # Spot-check one rate that differs between safety and general
    assert (
        abs(cm_via_loader.get_rate(30, 2022, False)
            - cm_safety.get_rate(30, 2022, False)) < 1e-12
    ), f"{class_name} should load the safety table via base_table_map"


# ---------------------------------------------------------------------------
# Bug 2 regression: compute_adjustment_ratio must handle long-format headcount
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("class_name", ["regular", "special", "admin",
                                        "senior_management"])
def test_adj_ratio_handles_long_format(class_name, frs_config):
    """`compute_adjustment_ratio` must sum the 'count' column for stage 3
    long-format headcount, not `iloc[:, 1:].sum().sum()` which would add
    the yos column values to the count.

    Guards against: stage 3 headcount shape (age, yos, count) being summed
    with the legacy wide-format logic, which silently inflates the
    denominator by the sum of yos values and deflates adj_ratio by ~0.3%.
    """
    from pension_model.core.pipeline import compute_adjustment_ratio

    demo_dir = Path(__file__).parent.parent.parent / "plans" / "frs" / "data" / "demographics"
    if not demo_dir.exists():
        pytest.skip("Stage 3 demographics not available")

    hc_long = pd.read_csv(demo_dir / f"{class_name}_headcount.csv")
    assert "count" in hc_long.columns, "stage 3 headcount must have count column"

    adj = compute_adjustment_ratio(class_name, hc_long, frs_config)

    # Independently compute expected value
    expected_denom = float(hc_long["count"].sum())
    expected_adj = (frs_config.class_data[class_name].total_active_member
                    / expected_denom)

    assert abs(adj - expected_adj) < 1e-12, (
        f"{class_name}: adj_ratio={adj} but expected {expected_adj} "
        f"from count.sum()={expected_denom}"
    )


# ---------------------------------------------------------------------------
# Bug 3 regression: admin must use regular-group design ratios (matching R)
# ---------------------------------------------------------------------------

def test_admin_design_ratios_match_r(frs_config):
    """Admin must get regular-group DB design ratios (0.75, 0.25, 0.25),
    NOT special-group (0.95, 0.85, 0.75), even though admin is in
    special_group for tier eligibility. See GH issue #22.

    R's liability model uses a hardcoded `if (class_name == "special")`
    string check, so only the literal 'special' class gets special ratios.
    Admin falls through to the non-special branch.
    """
    ratios = frs_config.get_design_ratios("admin")
    assert ratios["db"] == (0.75, 0.25, 0.25), (
        f"admin must use regular-group DB ratios, got {ratios['db']}. "
        f"Check design_ratio_group_map in plan_config.json."
    )


def test_special_still_uses_special_design_ratios(frs_config):
    """Sanity check: the design_ratio_group_map override must not affect
    the 'special' class itself, which really does use special-group ratios
    (0.95, 0.85, 0.75) in R."""
    ratios = frs_config.get_design_ratios("special")
    assert ratios["db"] == (0.95, 0.85, 0.75), (
        f"special must use special-group DB ratios, got {ratios['db']}"
    )


# ---------------------------------------------------------------------------
# End-to-end: stage 3 pipeline must reproduce R's total_aal_est exactly
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def stage3_liability(frs_config):
    """Run the stage 3 liability pipeline once for all FRS classes."""
    from pension_model.core.pipeline import run_plan_pipeline

    return run_plan_pipeline(frs_config)


@pytest.mark.parametrize("class_name", FRS_CLASSES)
def test_stage3_total_aal_matches_r_year_1(class_name, stage3_liability):
    """The stage 3 pipeline must reproduce R's total_aal_est at year 1
    to within $1 for every FRS class.

    This is the single most important reproduction test: it catches any
    bug anywhere in the stage 3 loading, benefit-table building, workforce
    projection, or liability computation that causes a year-0/1 divergence.
    """
    py = stage3_liability[class_name]
    r = pd.read_csv(FRS_BASELINES / f"{class_name}_liability.csv")

    py_val = float(py["total_aal_est"].iloc[0])
    r_val = float(r["total_aal_est"].iloc[0])

    assert abs(py_val - r_val) < 1.0, (
        f"{class_name} year-1 total_aal_est: Py={py_val:.2f} "
        f"R={r_val:.2f} diff={py_val - r_val:+.2f}"
    )


@pytest.mark.parametrize("class_name", FRS_CLASSES)
def test_stage3_total_aal_matches_r_year_30(class_name, stage3_liability):
    """The stage 3 pipeline must reproduce R's total_aal_est at year 30
    for every FRS class. Catches trajectory drift that wouldn't be visible
    at year 1 (e.g., a wrong growth/mortality/tier-assignment rule applied
    to projected cohorts).
    """
    py = stage3_liability[class_name]
    r = pd.read_csv(FRS_BASELINES / f"{class_name}_liability.csv")

    assert len(py) > 30, f"{class_name} pipeline produced fewer than 31 rows"
    assert len(r) > 30, f"{class_name} R baseline has fewer than 31 rows"

    py_val = float(py["total_aal_est"].iloc[30])
    r_val = float(r["total_aal_est"].iloc[30])

    assert abs(py_val - r_val) < 1.0, (
        f"{class_name} year-30 total_aal_est: Py={py_val:.2f} "
        f"R={r_val:.2f} diff={py_val - r_val:+.2f}"
    )


def test_unknown_retirement_rate_set_raises(frs_config, tmp_path):
    """A tier declaring a retirement_rate_set not in the CSV must raise
    a clear ValueError. Catches typos and broken refactors that today's
    silent-fallback code would absorb without warning.
    """
    from dataclasses import replace
    import pandas as pd
    from pension_model.core.data_loader import _build_yos_only_decrements

    # Force one tier to declare an unknown rate set. _tier_id_to_retire_rate_set
    # is a tuple[str, ...] cached on PlanConfig.
    bogus = replace(
        frs_config,
        _tier_id_to_retire_rate_set=("before_2011", "bogus_set", "2011_or_later"),
    )

    # A valid term_df shape with the lookup_type column the loader keys on
    term_df = pd.DataFrame({
        "lookup_type": ["yos"] * 2,
        "lookup_value": [0, 1],
        "age": [25, 26],
        "term_rate": [0.1, 0.1],
    })
    # ret_df has only the rate sets FRS already declares — bogus_set is missing
    ret_df = pd.DataFrame({
        "age": [55, 55],
        "rate_set": ["before_2011", "2011_or_later"],
        "retire_type": ["normal", "normal"],
        "retire_rate": [0.05, 0.04],
    })

    with pytest.raises(ValueError, match="bogus_set"):
        _build_yos_only_decrements(
            {}, bogus, term_df, ret_df, tmp_path, "regular"
        )


def test_unknown_decrements_method_raises():
    """A plan declaring an unknown decrements.method must raise a clear
    error at config-load time. The Decrements typed model uses a
    Literal["yos_only", "years_from_nr"] type, so any other value
    fails validation before reaching the dispatch in _load_decrements.
    """
    from pydantic import ValidationError
    from pension_model.schemas import Decrements

    with pytest.raises(ValidationError, match="made_up_method"):
        Decrements.model_validate({"method": "made_up_method"})


def test_overlapping_funding_legs_raises(frs_config):
    """Funding legs whose entry-year ranges overlap raise a clear
    ValueError listing the overlapping leg names.
    """
    from dataclasses import replace
    from pension_model.config_validation import validate_funding_legs

    # Override raw so funding_legs resolves to two overlapping legs.
    raw = dict(frs_config.raw)
    raw["funding"] = dict(raw["funding"])
    raw["funding"]["legs"] = [
        {"name": "legacy", "entry_year_max": 2030},
        {"name": "new", "entry_year_min": 2020},  # overlap on 2020-2029
    ]
    bogus = replace(frs_config, raw=raw)

    with pytest.raises(ValueError, match="overlap"):
        validate_funding_legs(bogus)


def test_gappy_funding_legs_raises(frs_config):
    """Funding legs that don't cover the full entry-year range raise a
    clear ValueError naming the uncovered year.
    """
    from dataclasses import replace
    from pension_model.config_validation import validate_funding_legs

    raw = dict(frs_config.raw)
    raw["funding"] = dict(raw["funding"])
    raw["funding"]["legs"] = [
        {"name": "legacy", "entry_year_max": 2010},
        {"name": "new", "entry_year_min": 2020},  # gap 2010..2019
    ]
    bogus = replace(frs_config, raw=raw)

    with pytest.raises(ValueError, match="not covered"):
        validate_funding_legs(bogus)


def test_unknown_tier_discount_rate_key_raises(frs_config):
    """A tier declaring a discount_rate_key not present on the
    economic namespace raises ValueError naming the unknown key.
    Catches typos and silent fallback to dr_current.
    """
    from pension_model.core.benefit_tables import _resolve_econ_rate

    econ = frs_config.economic
    with pytest.raises(ValueError, match="bogus_rate"):
        _resolve_econ_rate(econ, "bogus_rate", frs_config.plan_name)


def test_missing_per_class_nra_raises(frs_config):
    """A per-class NRA map missing the requested class and the
    'default' fallback raises a clear ValueError. Catches forgetting
    to declare an NRA for one of the plan's classes.
    """
    from dataclasses import replace
    from pension_model.config_resolvers import get_reduce_factor

    # FRS tier_1 uses a per-class NRA map. Build a tier_defs tuple with
    # tier_1's 'default' entry stripped — only 'special' is left.
    new_tier_defs = []
    for td in frs_config.tier_defs:
        if td["name"] == "tier_1":
            td2 = {**td, "early_retire_reduction": {**td["early_retire_reduction"]}}
            td2["early_retire_reduction"]["nra"] = {"special": 55}  # no 'default'
            new_tier_defs.append(td2)
        else:
            new_tier_defs.append(td)
    bogus = replace(frs_config, tier_defs=tuple(new_tier_defs))

    # 'regular' isn't in the map and no default — should raise.
    with pytest.raises(ValueError, match="no 'default'"):
        get_reduce_factor(
            bogus, "regular", "tier_1", "early", dist_age=58, yos=10, entry_year=1990
        )


def test_unknown_contribution_strategy_raises(frs_config):
    """A plan declaring funding.contribution_strategy = 'made_up' raises
    a clear ValueError from resolve_funding_context.
    """
    from dataclasses import replace
    from pension_model.core._funding_setup import resolve_funding_context

    bogus = replace(frs_config, contribution_strategy="made_up_strategy")
    funding_inputs = {
        "init_funding": __import__("pandas").DataFrame({"class": ["regular"]}),
    }

    with pytest.raises(ValueError, match="made_up_strategy"):
        resolve_funding_context(bogus, funding_inputs)


def test_statutory_strategy_requires_rates_block(frs_config):
    """Declaring funding.contribution_strategy = 'statutory' without a
    funding.statutory_rates block raises a clear ValueError.
    """
    from dataclasses import replace
    from pension_model.core._funding_setup import resolve_funding_context

    bogus = replace(frs_config, contribution_strategy="statutory")
    # FRS doesn't have statutory_rates; bogus inherits that absence.
    funding_inputs = {
        "init_funding": __import__("pandas").DataFrame({"class": ["regular"]}),
    }

    with pytest.raises(ValueError, match="statutory_rates"):
        resolve_funding_context(bogus, funding_inputs)


def test_missing_rule_nra_raises(frs_config):
    """A linear early-retire reduction rule without an 'nra' field
    raises a clear ValueError. Catches forgetting the NRA on a rule.
    """
    from dataclasses import replace
    from pension_model.config_resolvers import get_reduce_factor

    # Inject a tier with a linear rule that omits 'nra'.
    bogus_tier = {
        "name": "tier_bogus",
        "entry_year_min": 0,
        "entry_year_max": 9999,
        "fas_years": 5,
        "cola_key": "tier_1_active",
        "retirement_rate_set": "before_2011",
        "eligibility": {
            "default": {
                "normal": [{"min_age": 65}],
                "early": [{"min_age": 55}],
                "vesting_yos": 5,
            }
        },
        "early_retire_reduction": {
            "rules": [
                {"condition": {}, "formula": "linear", "rate_per_year": 0.05},  # no 'nra'
            ]
        },
    }
    bogus = replace(frs_config, tier_defs=(bogus_tier,))

    with pytest.raises(ValueError, match="without an 'nra' field"):
        get_reduce_factor(
            bogus, "regular", "tier_bogus", "early", dist_age=58, yos=10, entry_year=1990
        )
