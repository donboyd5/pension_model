"""
Truth table tests: verify Python-side truth table construction produces
valid DataFrames with the canonical column set and reasonable values.

These tests serve as a regression safety net — if pipeline output structure
changes, truth table construction should still work.
"""

import pytest

from pension_model.truth_table import (
    TRUTH_TABLE_COLUMNS,
    build_python_truth_table,
)


# ---------------------------------------------------------------------------
# FRS truth table
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def frs_truth_table():
    """Run FRS pipeline and build truth table."""
    from pension_model.core.pipeline import run_plan_pipeline
    from pension_model.core.funding_model import load_funding_inputs, compute_funding
    from pension_model.plan_config import load_frs_config

    constants = load_frs_config()
    liability = run_plan_pipeline(constants)
    funding_dir = constants.resolve_data_dir() / "funding"
    funding_inputs = load_funding_inputs(funding_dir)
    funding = compute_funding(liability, funding_inputs, constants)
    return build_python_truth_table("frs", liability, funding, constants)


def test_frs_truth_table_columns(frs_truth_table):
    """FRS truth table has exactly the canonical columns in order."""
    assert list(frs_truth_table.columns) == TRUTH_TABLE_COLUMNS


def test_frs_truth_table_rows(frs_truth_table):
    """FRS truth table has 31 rows (year 0 through 30)."""
    assert len(frs_truth_table) == 31


def test_frs_truth_table_plan_column(frs_truth_table):
    """FRS truth table plan column is 'frs'."""
    assert (frs_truth_table["plan"] == "frs").all()


def test_frs_truth_table_no_nan_in_required(frs_truth_table):
    """Required columns (not n_retired/n_inactive) should have no NaN."""
    required = ["year", "n_active_boy", "payroll_fy", "benefits_fy",
                "aal_boy", "er_cont_fy", "mva_boy", "ava_boy",
                "fr_mva_boy", "fr_ava_boy"]
    for col in required:
        assert frs_truth_table[col].notna().all(), f"{col} has NaN values"


def test_frs_truth_table_positive_values(frs_truth_table):
    """Key financial columns should be positive."""
    for col in ["payroll_fy", "aal_boy", "mva_boy", "ava_boy"]:
        vals = frs_truth_table[col].dropna()
        assert (vals > 0).all(), f"{col} has non-positive values"


def test_frs_truth_table_funded_ratio_bounded(frs_truth_table):
    """Funded ratios should be between 0 and 2."""
    for col in ["fr_mva_boy", "fr_ava_boy"]:
        vals = frs_truth_table[col].dropna()
        assert (vals > 0).all(), f"{col} has non-positive values"
        assert (vals < 2).all(), f"{col} has values >= 200%"


# ---------------------------------------------------------------------------
# TRS truth table
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def txtrs_truth_table():
    """Run TRS pipeline and build truth table."""
    from pension_model.core.pipeline import run_plan_pipeline
    from pension_model.core.funding_model import load_funding_inputs, compute_funding_trs
    from pension_model.plan_config import load_txtrs_config

    constants = load_txtrs_config()
    liability = run_plan_pipeline(constants)
    funding_dir = constants.resolve_data_dir() / "funding"
    funding_inputs = load_funding_inputs(funding_dir)
    # TRS funding takes the single-class DataFrame, not the dict
    first_class = list(constants.classes)[0]
    funding = compute_funding_trs(liability[first_class], funding_inputs, constants)
    return build_python_truth_table("txtrs", liability, funding, constants)


def test_txtrs_truth_table_columns(txtrs_truth_table):
    """TRS truth table has exactly the canonical columns in order."""
    assert list(txtrs_truth_table.columns) == TRUTH_TABLE_COLUMNS


def test_txtrs_truth_table_rows(txtrs_truth_table):
    """TRS truth table has 31 rows (year 0 through 30)."""
    assert len(txtrs_truth_table) == 31


def test_txtrs_truth_table_plan_column(txtrs_truth_table):
    """TRS truth table plan column is 'txtrs'."""
    assert (txtrs_truth_table["plan"] == "txtrs").all()


def test_txtrs_truth_table_no_nan_in_required(txtrs_truth_table):
    """Required columns should have no NaN."""
    required = ["year", "n_active_boy", "payroll_fy", "benefits_fy",
                "aal_boy", "er_cont_fy", "mva_boy", "ava_boy",
                "fr_mva_boy", "fr_ava_boy"]
    for col in required:
        assert txtrs_truth_table[col].notna().all(), f"{col} has NaN values"


def test_txtrs_truth_table_positive_values(txtrs_truth_table):
    """Key financial columns should be positive."""
    for col in ["payroll_fy", "aal_boy", "mva_boy", "ava_boy"]:
        vals = txtrs_truth_table[col].dropna()
        assert (vals > 0).all(), f"{col} has non-positive values"


def test_txtrs_truth_table_funded_ratio_bounded(txtrs_truth_table):
    """Funded ratios should be between 0 and 2."""
    for col in ["fr_mva_boy", "fr_ava_boy"]:
        vals = txtrs_truth_table[col].dropna()
        assert (vals > 0).all(), f"{col} has non-positive values"
        assert (vals < 2).all(), f"{col} has values >= 200%"
