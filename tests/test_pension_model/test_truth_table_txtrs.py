"""TXTRS truth table tests."""

import pytest

pytestmark = [pytest.mark.invariant, pytest.mark.regression]

from pension_model.truth_table import (
    TRUTH_TABLE_COLUMNS,
    build_python_truth_table,
)


@pytest.fixture(scope="module")
def txtrs_truth_table():
    """Run the TXTRS pipeline and build the truth table."""
    from pension_model.core.pipeline import run_plan_pipeline
    from pension_model.core.funding_model import load_funding_inputs, run_funding_model
    from pension_model.plan_config import load_txtrs_config

    constants = load_txtrs_config()
    liability = run_plan_pipeline(constants)
    funding_dir = constants.resolve_data_dir() / "funding"
    funding_inputs = load_funding_inputs(funding_dir)
    funding = run_funding_model(liability, funding_inputs, constants)
    return build_python_truth_table("txtrs", liability, funding, constants)


def test_txtrs_truth_table_columns(txtrs_truth_table):
    """TXTRS truth table has exactly the canonical columns in order."""
    assert list(txtrs_truth_table.columns) == TRUTH_TABLE_COLUMNS


def test_txtrs_truth_table_rows(txtrs_truth_table):
    """TXTRS truth table has 31 rows (year 0 through 30)."""
    assert len(txtrs_truth_table) == 31


def test_txtrs_truth_table_plan_column(txtrs_truth_table):
    """TXTRS truth table plan column is 'txtrs'."""
    assert (txtrs_truth_table["plan"] == "txtrs").all()


def test_txtrs_truth_table_no_nan_in_required(txtrs_truth_table):
    """Required columns should have no NaN."""
    required = ["year", "n_active_boy", "payroll", "benefits",
                "aal_boy", "mva_boy", "mva_eoy", "ava_boy",
                "fr_mva_boy", "fr_ava_boy"]
    for col in required:
        assert txtrs_truth_table[col].notna().all(), f"{col} has NaN values"


def test_txtrs_truth_table_positive_values(txtrs_truth_table):
    """Key financial columns should be positive."""
    for col in ["payroll", "aal_boy", "mva_boy", "ava_boy"]:
        vals = txtrs_truth_table[col].dropna()
        assert (vals > 0).all(), f"{col} has non-positive values"


def test_txtrs_truth_table_funded_ratio_bounded(txtrs_truth_table):
    """Funded ratios should be between 0 and 2."""
    for col in ["fr_mva_boy", "fr_ava_boy"]:
        vals = txtrs_truth_table[col].dropna()
        assert (vals > 0).all(), f"{col} has non-positive values"
        assert (vals < 2).all(), f"{col} has values >= 200%"


def test_txtrs_mva_balance(txtrs_truth_table):
    """mva_eoy should equal next row's mva_boy (MVA balance identity)."""
    tt = txtrs_truth_table
    for i in range(len(tt) - 1):
        mva_eoy = tt.iloc[i]["mva_eoy"]
        mva_boy_next = tt.iloc[i + 1]["mva_boy"]
        assert abs(mva_eoy - mva_boy_next) < 1.0, (
            f"Year {int(tt.iloc[i]['year'])}: mva_eoy={mva_eoy:.0f} != "
            f"next mva_boy={mva_boy_next:.0f}"
        )
