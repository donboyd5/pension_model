"""Output uniformity assertions.

Per ``meta-docs/repo_goals.md``: "all plans produce the same columns in
the same order; inapplicable values are NA." Today the canonical column
lists (``cli.SUMMARY_COLUMNS``, ``truth_table.TRUTH_TABLE_COLUMNS``)
declare those columns, but nothing fails if a plan silently fails to
populate one — ``cli._safe`` fills missing columns with ``NaN``.

This module enforces the contract:

* Every canonical column must be present in the output.
* Every column not declared inapplicable on the plan must have no NaN
  values across the projection horizon.
* Every column declared inapplicable must be entirely NaN (catches the
  inverse error of populating a column the plan claims it doesn't have).

Plans declare structural exceptions on :class:`PlanConfig` via the
``inapplicable_summary_columns`` and ``inapplicable_truth_table_columns``
fields. Today both reference plans (FRS, TXTRS) declare neither and
populate every column.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import pandas as pd


class OutputUniformityError(AssertionError):
    """Canonical-output column failed the uniformity contract."""


def _missing_columns(df: pd.DataFrame, expected: Sequence[str]) -> list[str]:
    return [c for c in expected if c not in df.columns]


def _columns_with_any_nan(df: pd.DataFrame, columns: Iterable[str]) -> dict[str, list[int]]:
    """Return ``{column: [row_indices_with_nan]}`` for columns containing NaN."""
    out: dict[str, list[int]] = {}
    for col in columns:
        mask = df[col].isna()
        if mask.any():
            out[col] = mask.to_numpy().nonzero()[0].tolist()
    return out


def _columns_not_all_nan(df: pd.DataFrame, columns: Iterable[str]) -> list[str]:
    return [col for col in columns if not df[col].isna().all()]


def assert_output_uniformity(
    df: pd.DataFrame,
    canonical_columns: Sequence[str],
    inapplicable: Sequence[str],
    *,
    plan_name: str,
    output_name: str,
) -> None:
    """Assert that ``df`` matches the canonical column contract.

    Parameters
    ----------
    df:
        Output frame to check.
    canonical_columns:
        The list of columns the contract requires.
    inapplicable:
        Columns the plan declares structurally inapplicable.
    plan_name:
        Plan name, included in error messages.
    output_name:
        Human-readable label for the artifact (e.g. ``"summary"``).

    Raises
    ------
    OutputUniformityError
        If any required column is missing, populated columns have NaN
        values, or columns declared inapplicable are populated.
    """
    missing = _missing_columns(df, canonical_columns)
    if missing:
        raise OutputUniformityError(
            f"[{plan_name} {output_name}] missing canonical columns: " f"{missing}"
        )

    inapplicable_set = set(inapplicable)
    unknown_inapplicable = inapplicable_set - set(canonical_columns)
    if unknown_inapplicable:
        raise OutputUniformityError(
            f"[{plan_name} {output_name}] inapplicable list names "
            f"non-canonical columns: {sorted(unknown_inapplicable)}"
        )

    required = [c for c in canonical_columns if c not in inapplicable_set]
    nan_offenders = _columns_with_any_nan(df, required)
    if nan_offenders:
        details = ", ".join(
            f"{col} (rows {rows[:5]}{'...' if len(rows) > 5 else ''})"
            for col, rows in nan_offenders.items()
        )
        raise OutputUniformityError(
            f"[{plan_name} {output_name}] required columns contain NaN: "
            f"{details}. If a column is structurally inapplicable to this "
            f"plan, declare it in inapplicable_{output_name}_columns."
        )

    populated_inapplicable = _columns_not_all_nan(df, inapplicable)
    if populated_inapplicable:
        raise OutputUniformityError(
            f"[{plan_name} {output_name}] columns declared inapplicable "
            f"but populated: {populated_inapplicable}. Either remove them "
            f"from inapplicable_{output_name}_columns or stop populating "
            f"them."
        )
