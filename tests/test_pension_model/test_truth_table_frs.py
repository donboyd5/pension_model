"""FRS truth table tests."""

import pytest

from pension_model.truth_table import (
    TRUTH_TABLE_COLUMNS,
    build_python_truth_table,
)

pytestmark = [pytest.mark.invariant, pytest.mark.regression]


@pytest.fixture(scope="module")
def frs_truth_table():
    """Run the FRS pipeline and build the truth table."""
    from pension_model.core.funding_model import load_funding_inputs, run_funding_model
    from pension_model.core.pipeline import run_plan_pipeline
    from pension_model.plan_config import load_plan_config_by_name

    constants = load_plan_config_by_name("frs")
    liability = run_plan_pipeline(constants)
    funding_dir = constants.resolve_data_dir() / "funding"
    funding_inputs = load_funding_inputs(funding_dir)
    funding = run_funding_model(liability, funding_inputs, constants)
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
    """Required columns should have no NaN."""
    required = [
        "year",
        "n_active_boy",
        "payroll",
        "benefits",
        "aal_boy",
        "mva_boy",
        "mva_eoy",
        "ava_boy",
        "fr_mva_boy",
        "fr_ava_boy",
    ]
    for col in required:
        assert frs_truth_table[col].notna().all(), f"{col} has NaN values"


def test_frs_truth_table_positive_values(frs_truth_table):
    """Key financial columns should be positive."""
    for col in ["payroll", "aal_boy", "mva_boy", "ava_boy"]:
        vals = frs_truth_table[col].dropna()
        assert (vals > 0).all(), f"{col} has non-positive values"


def test_frs_truth_table_funded_ratio_bounded(frs_truth_table):
    """Funded ratios should be between 0 and 2."""
    for col in ["fr_mva_boy", "fr_ava_boy"]:
        vals = frs_truth_table[col].dropna()
        assert (vals > 0).all(), f"{col} has non-positive values"
        assert (vals < 2).all(), f"{col} has values >= 200%"


def test_frs_mva_balance(frs_truth_table):
    """mva_eoy should equal next row's mva_boy (MVA balance identity)."""
    tt = frs_truth_table
    for i in range(len(tt) - 1):
        mva_eoy = tt.iloc[i]["mva_eoy"]
        mva_boy_next = tt.iloc[i + 1]["mva_boy"]
        assert abs(mva_eoy - mva_boy_next) < 1.0, (
            f"Year {int(tt.iloc[i]['year'])}: mva_eoy={mva_eoy:.0f} != "
            f"next mva_boy={mva_boy_next:.0f}"
        )
