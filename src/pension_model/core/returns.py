"""Investment return stream used by funding and cash-balance crediting.

Builds the year-indexed series of annual investment returns once per run.
The same series is used by:
  * the DB asset roll-forward (MVA, AVA smoothing, solvency contribution)
  * the cash-balance interest crediting calculation

By default the series is flat at ``constants.model_return``. Scenarios may
also provide ``economic.asset_return_path`` with projection-year keys and
numeric values or the token ``"model_return"``.
"""

import pandas as pd

from pension_model.config_schema import PlanConfig


def _resolve_return_value(value: float | int | str, constants: PlanConfig) -> float:
    """Resolve an asset-return-path value to a numeric annual return."""
    if value == "model_return":
        return float(constants.model_return)
    return float(value)


def build_return_stream(constants: PlanConfig) -> pd.Series:
    """Return a year-indexed series of annual investment returns.

    The index spans every year that any consumer might ask about
    (``min_entry_year`` through ``max_year``). Without an
    ``asset_return_path``, values are ``model_return`` at every year.
    With an ``asset_return_path``, integer keys are projection years
    relative to ``start_year``: key ``"1"`` applies to
    ``start_year + 1``.
    """
    years = range(constants.min_entry_year, constants.max_year + 1)
    path = constants.asset_return_path
    if not path:
        return pd.Series(constants.model_return, index=list(years), name="return")

    default = _resolve_return_value(path.get("default", "model_return"), constants)
    stream = pd.Series(default, index=list(years), name="return")
    for key, value in path.items():
        if key == "default":
            continue
        year = constants.start_year + int(key)
        if year in stream.index:
            stream.loc[year] = _resolve_return_value(value, constants)
    return stream
