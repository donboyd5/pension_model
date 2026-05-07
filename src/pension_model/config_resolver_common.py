"""Shared helper logic for config-derived scalar and vectorized resolvers."""

from pension_model.config_schema import EARLY, NON_VESTED, NORM, VESTED

import numpy as np


def _matches_condition(
    cond: dict,
    age: int,
    yos: int,
    entry_year: int = 0,
    entry_age: int = 0,
) -> bool:
    if "min_age" in cond and age < cond["min_age"]:
        return False
    if "min_yos" in cond and yos < cond["min_yos"]:
        return False
    if "rule_of" in cond and (age + yos) < cond["rule_of"]:
        return False
    return True


def _matches_any(
    rules: list,
    age: int,
    yos: int,
    entry_year: int = 0,
    entry_age: int = 0,
) -> bool:
    for rule in rules:
        if _matches_condition(rule, age, yos, entry_year, entry_age):
            return True
    return False


def _resolve_tier_def(tier_name: str, tier_defs: tuple) -> dict:
    for tier_def in tier_defs:
        if tier_def["name"] == tier_name:
            return tier_def
    raise ValueError(f"Unknown tier: {tier_name}")


def _get_eligibility(tier_def: dict, group: str, all_tier_defs: tuple):
    """Resolve a tier's eligibility for ``group`` to a typed
    :class:`EligibilitySpec`, following ``eligibility_same_as``
    references. Returns None when no matching eligibility (or
    ``default`` fallback) exists — today this happens only for
    DROP-shaped tier defs and similar edge cases.
    """
    from pension_model.schemas import EligibilitySpec  # local to avoid cycle

    current = tier_def
    seen = set()
    while "eligibility_same_as" in current:
        ref = current["eligibility_same_as"]
        if ref in seen:
            raise ValueError(f"Circular eligibility_same_as: {ref}")
        seen.add(ref)
        current = _resolve_tier_def(ref, all_tier_defs)

    eligibility = current["eligibility"]
    raw = eligibility.get(group, eligibility.get("default"))
    if raw is None:
        return None
    return EligibilitySpec.model_validate(raw)


def _entry_year_in_tier(entry_year: int, tier_def: dict, new_year: int) -> bool:
    if tier_def.get("assignment") == "grandfathered_rule":
        return False

    lo = tier_def.get("entry_year_min")
    if tier_def.get("entry_year_min_param") == "new_year":
        lo = new_year

    hi = tier_def.get("entry_year_max")
    if tier_def.get("entry_year_max_param") == "new_year":
        hi = new_year

    if lo is not None and entry_year < lo:
        return False
    if hi is not None and entry_year >= hi:
        return False
    return True


def _is_grandfathered(entry_year: int, entry_age: int, params: dict) -> bool:
    cutoff = params["cutoff_year"]
    if entry_year > cutoff:
        return False
    yos_at_cutoff = min(cutoff - entry_year, 70)
    age_at_cutoff = entry_age + yos_at_cutoff
    for cond in params["conditions"]:
        if "min_age_at_cutoff" in cond and age_at_cutoff >= cond["min_age_at_cutoff"]:
            return True
        if "rule_of_at_cutoff" in cond and (age_at_cutoff + yos_at_cutoff) >= cond["rule_of_at_cutoff"]:
            return True
        if "min_yos_at_cutoff" in cond and yos_at_cutoff >= cond["min_yos_at_cutoff"]:
            return True
    return False


def _check_reduce_condition(
    cond: dict,
    dist_age: int,
    yos: int,
    entry_year: int,
    tier_name: str,
) -> bool:
    if not cond:
        return True
    if "min_yos" in cond and yos < cond["min_yos"]:
        return False
    if "min_age" in cond and dist_age < cond["min_age"]:
        return False
    if "rule_of" in cond and (dist_age + yos) < cond["rule_of"]:
        return False
    if cond.get("grandfathered") and "grandfathered" not in tier_name:
        return False
    if "or" in cond:
        return any(
            _check_reduce_condition(sub, dist_age, yos, entry_year, tier_name)
            for sub in cond["or"]
        )
    return True


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
            int_cols = [c for c in age_cols if isinstance(c, (int, float))]
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


def _entry_year_in_tier_vec(entry_year: np.ndarray, tier_def: dict, new_year: int) -> np.ndarray:
    if tier_def.get("assignment") == "grandfathered_rule":
        return np.zeros(len(entry_year), dtype=bool)

    lo = tier_def.get("entry_year_min")
    if tier_def.get("entry_year_min_param") == "new_year":
        lo = new_year
    hi = tier_def.get("entry_year_max")
    if tier_def.get("entry_year_max_param") == "new_year":
        hi = new_year

    mask = np.ones(len(entry_year), dtype=bool)
    if lo is not None:
        mask &= entry_year >= lo
    if hi is not None:
        mask &= entry_year < hi
    return mask


def _is_grandfathered_vec(entry_year: np.ndarray, entry_age: np.ndarray, params: dict) -> np.ndarray:
    cutoff = params["cutoff_year"]
    in_range = entry_year <= cutoff
    yos_at_cutoff = np.minimum(cutoff - entry_year, 70)
    age_at_cutoff = entry_age + yos_at_cutoff

    result = np.zeros(len(entry_year), dtype=bool)
    for cond in params["conditions"]:
        if "min_age_at_cutoff" in cond:
            result |= in_range & (age_at_cutoff >= cond["min_age_at_cutoff"])
        if "rule_of_at_cutoff" in cond:
            result |= in_range & ((age_at_cutoff + yos_at_cutoff) >= cond["rule_of_at_cutoff"])
        if "min_yos_at_cutoff" in cond:
            result |= in_range & (yos_at_cutoff >= cond["min_yos_at_cutoff"])
    return result


def _matches_condition_vec(cond: dict, age: np.ndarray, yos: np.ndarray) -> np.ndarray:
    mask = np.ones(len(age), dtype=bool)
    if "min_age" in cond:
        mask &= age >= cond["min_age"]
    if "min_yos" in cond:
        mask &= yos >= cond["min_yos"]
    if "rule_of" in cond:
        mask &= (age + yos) >= cond["rule_of"]
    return mask


def _matches_any_vec(rules: list, age: np.ndarray, yos: np.ndarray) -> np.ndarray:
    if not rules:
        return np.zeros(len(age), dtype=bool)
    result = np.zeros(len(age), dtype=bool)
    for rule in rules:
        result |= _matches_condition_vec(rule, age, yos)
    return result


def _resolve_ben_mult_rules(class_rules: dict, tier_base: str):
    if "all_tiers" in class_rules:
        return class_rules["all_tiers"]
    rules = class_rules.get(tier_base)
    if rules is None:
        for key in class_rules:
            if key.endswith("_same_as") and key.replace("_same_as", "") == tier_base:
                rules = class_rules.get(class_rules[key])
                break
    return rules


def _reduce_condition_vec(
    cond: dict,
    dist_age: np.ndarray,
    yos: np.ndarray,
    entry_year: np.ndarray,
    tier_name: str,
) -> np.ndarray:
    if not cond:
        return np.ones(len(dist_age), dtype=bool)
    mask = np.ones(len(dist_age), dtype=bool)
    if "min_yos" in cond:
        mask &= yos >= cond["min_yos"]
    if "min_age" in cond:
        mask &= dist_age >= cond["min_age"]
    if "rule_of" in cond:
        mask &= (dist_age + yos) >= cond["rule_of"]
    if cond.get("grandfathered") and "grandfathered" not in tier_name:
        mask &= False
    if "or" in cond:
        or_mask = np.zeros(len(dist_age), dtype=bool)
        for sub in cond["or"]:
            or_mask |= _reduce_condition_vec(sub, dist_age, yos, entry_year, tier_name)
        mask &= or_mask
    return mask
