from __future__ import annotations

"""Scalar config-derived resolvers."""

from typing import TYPE_CHECKING

import numpy as np

from pension_model.config_resolver_common import (
    _check_reduce_condition,
    _entry_year_in_tier,
    _get_eligibility,
    _is_grandfathered,
    _lookup_reduce_table,
    _matches_any,
    _matches_condition,
    _resolve_tier_def,
)

if TYPE_CHECKING:
    from pension_model.config_schema import PlanConfig


def get_tier(
    config: PlanConfig,
    class_name: str,
    entry_year: int,
    age: int,
    yos: int,
    entry_age: int = 0,
) -> str:
    group = config.class_group(class_name)

    matched_tier = None
    for tier_def in config.tier_defs:
        if tier_def.get("assignment") == "grandfathered_rule":
            effective_entry_age = entry_age if entry_age > 0 else (age - yos)
            if _is_grandfathered(
                entry_year,
                effective_entry_age,
                tier_def["grandfathered_params"],
            ):
                matched_tier = tier_def
                break
        elif _entry_year_in_tier(entry_year, tier_def, config.new_year):
            if tier_def.get("not_grandfathered"):
                gf_tier = next(
                    (
                        tier
                        for tier in config.tier_defs
                        if tier.get("assignment") == "grandfathered_rule"
                    ),
                    None,
                )
                if gf_tier:
                    effective_entry_age = entry_age if entry_age > 0 else (age - yos)
                    if _is_grandfathered(
                        entry_year,
                        effective_entry_age,
                        gf_tier["grandfathered_params"],
                    ):
                        continue
            matched_tier = tier_def
            break

    if matched_tier is None:
        matched_tier = config.tier_defs[-1]

    tier_name = matched_tier["name"]
    eligibility = _get_eligibility(matched_tier, group, config.tier_defs)

    if not eligibility:
        return f"{tier_name}_non_vested"

    if _matches_any(eligibility.get("normal", []), age, yos, entry_year, entry_age):
        return f"{tier_name}_norm"

    if _matches_any(eligibility.get("early", []), age, yos, entry_year, entry_age):
        return f"{tier_name}_early"

    vesting_yos = eligibility["vesting_yos"]
    if yos >= vesting_yos:
        return f"{tier_name}_vested"

    return f"{tier_name}_non_vested"


def get_tier_vectorized(
    config: PlanConfig,
    class_name: str,
    entry_year: np.ndarray,
    age: np.ndarray,
    yos: np.ndarray,
    entry_age: np.ndarray = None,
) -> np.ndarray:
    n = len(entry_year)
    result = np.empty(n, dtype=object)
    effective_entry_age = entry_age if entry_age is not None else (age - yos)
    for i in range(n):
        result[i] = get_tier(
            config,
            class_name,
            int(entry_year[i]),
            int(age[i]),
            int(yos[i]),
            int(effective_entry_age[i]),
        )
    return result


def get_ben_mult(
    config: PlanConfig,
    class_name: str,
    tier: str,
    dist_age: int,
    yos: int,
    dist_year: int = 0,
) -> float:
    class_rules = config.benefit_mult_defs.get(class_name)
    if class_rules is None:
        return float("nan")

    tier_base = tier.split("_")[0] + "_" + tier.split("_")[1] if "_" in tier else tier

    if "all_tiers" in class_rules:
        rules = class_rules["all_tiers"]
    else:
        rules = class_rules.get(tier_base)
        if rules is None:
            for key in class_rules:
                if key.endswith("_same_as") and key.replace("_same_as", "") == tier_base:
                    rules = class_rules.get(class_rules[key])
                    break
        if rules is None:
            return float("nan")

    if "flat" in rules:
        if "flat_before_year" in rules and dist_year <= rules["flat_before_year"]["year"]:
            return rules["flat_before_year"]["mult"]
        return rules["flat"]

    if "graded" in rules:
        for entry in rules["graded"]:
            for cond in entry["or"]:
                if _matches_condition(cond, dist_age, yos):
                    return entry["mult"]
        if "early" in tier and "early_fallback" in rules:
            return rules["early_fallback"]
        return float("nan")

    return float("nan")


def get_reduce_factor(
    config: PlanConfig,
    class_name: str,
    tier: str,
    dist_age: int,
    yos: int = 0,
    entry_year: int = 0,
) -> float:
    if "norm" in tier:
        return 1.0
    if "early" not in tier and "reduced" not in tier:
        return float("nan")

    tier_name = tier.rsplit("_", 1)[0] if "_" in tier else tier
    tier_def = next((td for td in config.tier_defs if td["name"] == tier_name), None)
    if tier_def is None:
        return float("nan")

    reduction_def = tier_def
    seen = set()
    while "early_retire_reduction_same_as" in reduction_def:
        ref = reduction_def["early_retire_reduction_same_as"]
        if ref in seen:
            break
        seen.add(ref)
        reduction_def = _resolve_tier_def(ref, config.tier_defs)

    reduction = reduction_def.get("early_retire_reduction", {})

    if "nra" in reduction:
        nra_map = reduction["nra"]
        rate = reduction["rate_per_year"]
        nra = nra_map.get(class_name, nra_map.get("default", 65))
        return 1.0 - rate * (nra - dist_age)

    if "rules" in reduction:
        for rule in reduction["rules"]:
            condition = rule.get("condition", {})
            if not _check_reduce_condition(condition, dist_age, yos, entry_year, tier_name):
                continue
            formula = rule.get("formula", "linear")
            if formula == "linear":
                rate = rule["rate_per_year"]
                nra = rule.get("nra", 65)
                return max(0.0, 1.0 - rate * (nra - dist_age))
            if formula == "table":
                table_key = rule.get("table_key", "")
                if config.reduce_tables and table_key in config.reduce_tables:
                    return _lookup_reduce_table(config.reduce_tables[table_key], table_key, dist_age, yos)
                raise ValueError(
                    f"early-retire reduction rule references table_key={table_key!r} "
                    f"but no matching reduction table is loaded for plan {config.plan_name!r}. "
                    f"Provide the table CSV under the plan's data directory."
                )
        return float("nan")

    return float("nan")
