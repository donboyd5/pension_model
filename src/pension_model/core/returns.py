"""Investment return stream used by funding and cash-balance crediting.

Builds the year-indexed series of annual investment returns once per run.
The same series is used by:
  * the DB asset roll-forward (MVA, AVA smoothing, solvency contribution)
  * the cash-balance interest crediting calculation

Today the series is flat at ``constants.model_return``. A follow-up PR
will allow scenarios to specify a year-by-year path; the consumers will
not change.
"""

import pandas as pd

from pension_model.config_schema import PlanConfig


def build_return_stream(constants: PlanConfig) -> pd.Series:
    """Return a year-indexed series of annual investment returns.

    The index spans every year that any consumer might ask about
    (``min_entry_year`` through ``max_year``). Values are ``model_return``
    at every year. Scenarios that override ``economic.model_return``
    flow through automatically.
    """
    years = range(constants.min_entry_year, constants.max_year + 1)
    return pd.Series(constants.model_return, index=list(years), name="return")
