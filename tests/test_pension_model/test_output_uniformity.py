"""Output uniformity contract tests.

The runtime asserts that every plan populates every canonical column
in summary.csv and the truth table — except those a plan explicitly
declares structurally inapplicable.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pension_model.output_uniformity import (
    OutputUniformityError,
    assert_output_uniformity,
)

pytestmark = [pytest.mark.unit]


CANONICAL = ["plan", "year", "aal", "mva"]


def _good_frame():
    return pd.DataFrame(
        {
            "plan": ["frs"] * 3,
            "year": [2024, 2025, 2026],
            "aal": [1.0, 2.0, 3.0],
            "mva": [4.0, 5.0, 6.0],
        }
    )


def test_passes_when_all_columns_populated():
    df = _good_frame()
    assert_output_uniformity(
        df,
        CANONICAL,
        inapplicable=(),
        plan_name="frs",
        output_name="summary",
    )


def test_missing_canonical_column_caught():
    df = _good_frame().drop(columns=["aal"])
    with pytest.raises(OutputUniformityError) as excinfo:
        assert_output_uniformity(
            df,
            CANONICAL,
            inapplicable=(),
            plan_name="frs",
            output_name="summary",
        )
    assert "missing canonical columns" in str(excinfo.value)
    assert "aal" in str(excinfo.value)


def test_nan_in_required_column_caught():
    df = _good_frame()
    df.loc[1, "aal"] = np.nan
    with pytest.raises(OutputUniformityError) as excinfo:
        assert_output_uniformity(
            df,
            CANONICAL,
            inapplicable=(),
            plan_name="frs",
            output_name="summary",
        )
    msg = str(excinfo.value)
    assert "aal" in msg
    assert "rows [1]" in msg


def test_nan_allowed_when_column_declared_inapplicable():
    df = _good_frame()
    df["aal"] = np.nan
    assert_output_uniformity(
        df,
        CANONICAL,
        inapplicable=("aal",),
        plan_name="dc_only_plan",
        output_name="summary",
    )


def test_inapplicable_column_must_be_all_nan():
    df = _good_frame()
    df.loc[0, "aal"] = np.nan  # one NaN, rest populated
    with pytest.raises(OutputUniformityError) as excinfo:
        assert_output_uniformity(
            df,
            CANONICAL,
            inapplicable=("aal",),
            plan_name="dc_only_plan",
            output_name="summary",
        )
    assert "declared inapplicable but populated" in str(excinfo.value)


def test_inapplicable_must_be_in_canonical_list():
    df = _good_frame()
    with pytest.raises(OutputUniformityError) as excinfo:
        assert_output_uniformity(
            df,
            CANONICAL,
            inapplicable=("not_a_real_column",),
            plan_name="frs",
            output_name="summary",
        )
    assert "non-canonical" in str(excinfo.value)
