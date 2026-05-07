"""Shared helper logic for config-derived scalar and vectorized resolvers.

The Tier-aware predicate logic now lives on the typed schema models
themselves (``Tier.entry_year_in_window``, ``Tier.resolve_eligibility``,
``ReduceCondition.matches``, etc.). This module is the home for the
remaining helper — reduce-table CSV lookup.
"""


def _lookup_reduce_table(table, table_key: str, dist_age: int, yos: int) -> float:
    if "gft" in table_key.lower():
        row = table[table["yos"] == yos]
        if row.empty:
            row = table[table["yos"] <= yos].tail(1)
        if row.empty:
            return float("nan")
        age_cols = [c for c in table.columns if c != "yos"]
        age_col = int(dist_age) if int(dist_age) in age_cols else None
        if age_col is None:
            int_cols = [c for c in age_cols if isinstance(c, int | float)]
            if int_cols:
                age_col = min(int_cols, key=lambda x: abs(x - dist_age))
        if age_col is not None:
            val = row.iloc[0][age_col]
            if val is not None and not (isinstance(val, float) and val != val):
                return float(val)
        return float("nan")

    row = table[table["age"] == dist_age]
    if row.empty:
        return float("nan")
    col = [c for c in table.columns if c != "age"][0]
    return float(row.iloc[0][col])
