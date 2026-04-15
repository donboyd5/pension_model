from __future__ import annotations

"""Vectorized config-derived resolvers."""

from typing import Optional, TYPE_CHECKING, Tuple

import numpy as np

from pension_model.config_resolver_common import (
    EARLY,
    NON_VESTED,
    NORM,
    VESTED,
    _STATUS_SUFFIX,
    _default_reduce_factor,
    _entry_year_in_tier_vec,
    _get_eligibility,
    _is_grandfathered_vec,
    _lookup_reduce_table,
    _matches_any_vec,
    _matches_condition_vec,
    _reduce_condition_vec,
    _resolve_ben_mult_rules,
    _resolve_tier_def,
)

if TYPE_CHECKING:
    from pension_model.config_schema import PlanConfig


def resolve_tiers_vec(
    config: PlanConfig,
    class_name: np.ndarray,
    entry_year: np.ndarray,
    age: np.ndarray,
    yos: np.ndarray,
    entry_age: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    entry_year = np.asarray(entry_year, dtype=np.int64)
    age = np.asarray(age, dtype=np.int64)
    yos = np.asarray(yos, dtype=np.int64)

    if entry_age is None:
        effective_entry_age = age - yos
    else:
        effective_entry_age = np.asarray(entry_age, dtype=np.int64)
        effective_entry_age = np.where(effective_entry_age > 0, effective_entry_age, age - yos)

    group = np.array([config._class_to_group.get(cn, "default") for cn in class_name], dtype=object)

    gf_tier_def = next(
        (td for td in config.tier_defs if td.get("assignment") == "grandfathered_rule"),
        None,
    )
    gf_mask_global = (
        _is_grandfathered_vec(entry_year, effective_entry_age, gf_tier_def["grandfathered_params"])
        if gf_tier_def is not None
        else np.zeros(len(entry_year), dtype=bool)
    )

    tier_id = np.full(len(entry_year), -1, dtype=np.int32)
    for i, tier_def in enumerate(config.tier_defs):
        unassigned = tier_id == -1
        if not unassigned.any():
            break
        if tier_def.get("assignment") == "grandfathered_rule":
            mask = gf_mask_global & unassigned
        else:
            mask = _entry_year_in_tier_vec(entry_year, tier_def, config.new_year) & unassigned
            if tier_def.get("not_grandfathered"):
                mask &= ~gf_mask_global
        tier_id[mask] = i

    tier_id[tier_id == -1] = len(config.tier_defs) - 1

    ret_status = np.full(len(entry_year), NON_VESTED, dtype=np.int8)
    for tier_index, tier_def in enumerate(config.tier_defs):
        for grp in set(group.tolist()):
            combo_mask = (tier_id == tier_index) & (group == grp)
            if not combo_mask.any():
                continue
            eligibility = _get_eligibility(tier_def, grp, config.tier_defs)
            if not eligibility:
                continue

            sub_age = age[combo_mask]
            sub_yos = yos[combo_mask]
            norm_mask = _matches_any_vec(eligibility.get("normal", []), sub_age, sub_yos)
            early_mask = _matches_any_vec(eligibility.get("early", []), sub_age, sub_yos) & ~norm_mask
            vested_mask = (sub_yos >= eligibility.get("vesting_yos", 5)) & ~norm_mask & ~early_mask

            sub_status = np.full(combo_mask.sum(), NON_VESTED, dtype=np.int8)
            sub_status[norm_mask] = NORM
            sub_status[early_mask] = EARLY
            sub_status[vested_mask] = VESTED
            ret_status[combo_mask] = sub_status

    return tier_id, ret_status


def resolve_tiers_vec_str(
    config: PlanConfig,
    class_name: np.ndarray,
    entry_year: np.ndarray,
    age: np.ndarray,
    yos: np.ndarray,
    entry_age: Optional[np.ndarray] = None,
) -> np.ndarray:
    tier_id, ret_status = resolve_tiers_vec(config, class_name, entry_year, age, yos, entry_age)
    result = np.empty(len(tier_id), dtype=object)
    for i in range(len(tier_id)):
        result[i] = config._tier_id_to_name[tier_id[i]] + _STATUS_SUFFIX[ret_status[i]]
    return result


def resolve_cola_vec(
    config: PlanConfig,
    tier_id: np.ndarray,
    entry_year: np.ndarray,
    yos: np.ndarray,
) -> np.ndarray:
    tier_id = np.asarray(tier_id, dtype=np.int32)
    entry_year = np.asarray(entry_year, dtype=np.int64)
    yos = np.asarray(yos, dtype=np.int64)
    cola_cutoff = config.cola_proration_cutoff_year

    result = np.zeros(len(tier_id), dtype=np.float64)
    for i, tier_def in enumerate(config.tier_defs):
        mask = tier_id == i
        if not mask.any():
            continue
        cola_key = tier_def["cola_key"]
        raw_cola = config.cola.get(cola_key, 0.0)
        should_prorate = (
            tier_def.get("prorate_cola", False)
            and not config.cola.get(cola_key + "_constant", False)
            and cola_cutoff is not None
            and raw_cola > 0
        )
        if should_prorate:
            sub_entry_year = entry_year[mask]
            sub_yos = yos[mask]
            yos_b4 = np.minimum(np.maximum(cola_cutoff - sub_entry_year, 0), sub_yos)
            with np.errstate(divide="ignore", invalid="ignore"):
                safe_yos = np.where(sub_yos > 0, sub_yos, 1)
                prorated = raw_cola * yos_b4 / safe_yos
            result[mask] = np.where(sub_yos > 0, prorated, raw_cola)
        else:
            result[mask] = raw_cola
    return result


def resolve_ben_mult_vec(
    config: PlanConfig,
    class_name: np.ndarray,
    tier_id: np.ndarray,
    ret_status: np.ndarray,
    dist_age: np.ndarray,
    yos: np.ndarray,
    dist_year: np.ndarray,
) -> np.ndarray:
    import pandas as pd

    tier_id = np.asarray(tier_id, dtype=np.int32)
    ret_status = np.asarray(ret_status, dtype=np.int8)
    dist_age = np.asarray(dist_age, dtype=np.int64)
    yos = np.asarray(yos, dtype=np.int64)
    dist_year = np.asarray(dist_year, dtype=np.int64)

    result = np.full(len(tier_id), np.nan, dtype=np.float64)
    keys = pd.Series(
        list(
            zip(
                class_name.tolist() if hasattr(class_name, "tolist") else list(class_name),
                tier_id.tolist(),
            )
        )
    )
    for (class_name_value, tier_index), idx in keys.groupby(keys).groups.items():
        idx_arr = np.asarray(idx, dtype=np.int64)
        class_rules = config.benefit_mult_defs.get(class_name_value)
        if class_rules is None:
            continue
        rules = _resolve_ben_mult_rules(class_rules, config._tier_id_to_name[tier_index])
        if rules is None:
            continue

        sub_age = dist_age[idx_arr]
        sub_yos = yos[idx_arr]
        sub_year = dist_year[idx_arr]

        if "flat" in rules:
            vals = np.full(len(idx_arr), rules["flat"], dtype=np.float64)
            if "flat_before_year" in rules:
                before = rules["flat_before_year"]
                vals = np.where(sub_year <= before["year"], before["mult"], vals)
            result[idx_arr] = vals
            continue

        if "graded" in rules:
            sub_vals = np.full(len(idx_arr), np.nan, dtype=np.float64)
            assigned = np.zeros(len(idx_arr), dtype=bool)
            for entry in rules["graded"]:
                entry_mask = np.zeros(len(idx_arr), dtype=bool)
                for cond in entry["or"]:
                    entry_mask |= _matches_condition_vec(cond, sub_age, sub_yos)
                new_assign = entry_mask & ~assigned
                if new_assign.any():
                    sub_vals[new_assign] = entry["mult"]
                    assigned |= new_assign
            if "early_fallback" in rules:
                fallback_mask = ~assigned & (ret_status[idx_arr] == EARLY)
                sub_vals[fallback_mask] = rules["early_fallback"]
            result[idx_arr] = sub_vals

    return result


def resolve_reduce_factor_vec(
    config: PlanConfig,
    class_name: np.ndarray,
    tier_id: np.ndarray,
    ret_status: np.ndarray,
    dist_age: np.ndarray,
    yos: np.ndarray,
    entry_year: np.ndarray,
) -> np.ndarray:
    import pandas as pd

    tier_id = np.asarray(tier_id, dtype=np.int32)
    ret_status = np.asarray(ret_status, dtype=np.int8)
    dist_age = np.asarray(dist_age, dtype=np.int64)
    yos = np.asarray(yos, dtype=np.int64)
    entry_year = np.asarray(entry_year, dtype=np.int64)

    result = np.full(len(tier_id), np.nan, dtype=np.float64)
    result[ret_status == NORM] = 1.0
    needs_reduction = ret_status == EARLY
    if not needs_reduction.any():
        return result

    keys = pd.Series(list(zip(class_name.tolist(), tier_id.tolist())))[needs_reduction]
    for (class_name_value, tier_index), idx in keys.groupby(keys).groups.items():
        idx_arr = np.asarray(idx, dtype=np.int64)
        tier_def = config.tier_defs[tier_index]
        if tier_def is None:
            continue

        reduction_def = tier_def
        seen = set()
        while "early_retire_reduction_same_as" in reduction_def:
            ref = reduction_def["early_retire_reduction_same_as"]
            if ref in seen:
                break
            seen.add(ref)
            reduction_def = _resolve_tier_def(ref, config.tier_defs)

        reduction = reduction_def.get("early_retire_reduction", {})
        sub_age = dist_age[idx_arr]
        sub_yos = yos[idx_arr]
        sub_entry_year = entry_year[idx_arr]

        if "nra" in reduction:
            nra_map = reduction["nra"]
            rate = reduction["rate_per_year"]
            nra = nra_map.get(class_name_value, nra_map.get("default", 65))
            result[idx_arr] = 1.0 - rate * (nra - sub_age)
            continue

        if "rules" in reduction:
            sub_vals = np.full(len(idx_arr), np.nan, dtype=np.float64)
            assigned = np.zeros(len(idx_arr), dtype=bool)
            tier_name = config._tier_id_to_name[tier_index]
            for rule in reduction["rules"]:
                cond_mask = _reduce_condition_vec(
                    rule.get("condition", {}),
                    sub_age,
                    sub_yos,
                    sub_entry_year,
                    tier_name,
                )
                cond_mask &= ~assigned
                if not cond_mask.any():
                    continue
                formula = rule.get("formula", "linear")
                if formula == "linear":
                    rate = rule["rate_per_year"]
                    nra = rule.get("nra", 65)
                    sub_vals[cond_mask] = np.maximum(0.0, 1.0 - rate * (nra - sub_age[cond_mask]))
                    assigned |= cond_mask
                elif formula == "table":
                    table_key = rule.get("table_key", "")
                    for local_index in np.where(cond_mask)[0]:
                        if config.reduce_tables and table_key in config.reduce_tables:
                            sub_vals[local_index] = _lookup_reduce_table(
                                config.reduce_tables[table_key],
                                table_key,
                                int(sub_age[local_index]),
                                int(sub_yos[local_index]),
                            )
                        else:
                            sub_vals[local_index] = _default_reduce_factor(int(sub_age[local_index]))
                    assigned |= cond_mask
            result[idx_arr] = sub_vals

    return result
