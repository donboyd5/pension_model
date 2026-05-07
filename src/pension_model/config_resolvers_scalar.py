from __future__ import annotations

"""Scalar config-derived resolvers."""

from typing import TYPE_CHECKING

from pension_model.config_resolver_common import (
    _check_reduce_condition,
    _entry_year_in_tier,
    _get_eligibility,
    _is_grandfathered,
    _lookup_reduce_table,
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
) -> tuple[str, str]:
    """Resolve the (tier_name, status) for one (class, entry_year, age, yos).

    Status is one of ``"norm"``, ``"early"``, ``"vested"``, ``"non_vested"``.
    """
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

    if eligibility is None:
        return tier_name, "non_vested"

    if eligibility.matches_normal(age, yos):
        return tier_name, "norm"

    if eligibility.matches_early(age, yos):
        return tier_name, "early"

    if yos >= eligibility.vesting_yos:
        return tier_name, "vested"

    return tier_name, "non_vested"


def get_ben_mult(
    config: PlanConfig,
    class_name: str,
    tier_name: str,
    status: str,
    dist_age: int,
    yos: int,
    dist_year: int = 0,
) -> float:
    rules = config.resolve_ben_mult(class_name, tier_name)
    if rules is None:
        return float("nan")

    if rules.flat is not None:
        if rules.flat_before_year is not None and dist_year <= rules.flat_before_year.year:
            return rules.flat_before_year.mult
        return rules.flat

    if rules.graded is not None:
        for entry in rules.graded:
            for cond in entry.or_:
                if cond.matches(dist_age, yos):
                    return entry.mult
        if status == "early" and rules.early_fallback is not None:
            return rules.early_fallback
        return float("nan")

    return float("nan")


def get_reduce_factor(
    config: PlanConfig,
    class_name: str,
    tier_name: str,
    status: str,
    dist_age: int,
    yos: int = 0,
    entry_year: int = 0,
) -> float:
    if status == "norm":
        return 1.0
    if status != "early":
        return float("nan")

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
        if class_name in nra_map:
            nra = nra_map[class_name]
        elif "default" in nra_map:
            nra = nra_map["default"]
        else:
            raise ValueError(
                f"Plan {config.plan_name!r}: NRA map for tier "
                f"{tier_name!r} has no entry for class {class_name!r} "
                f"and no 'default' fallback. Add either an explicit "
                f"per-class NRA or a 'default' key to "
                f"early_retire_reduction.nra."
            )
        return 1.0 - rate * (nra - dist_age)

    if "rules" in reduction:
        for rule in reduction["rules"]:
            condition = rule.get("condition", {})
            if not _check_reduce_condition(condition, dist_age, yos, entry_year, tier_name):
                continue
            formula = rule.get("formula", "linear")
            if formula == "linear":
                rate = rule["rate_per_year"]
                if "nra" not in rule:
                    raise ValueError(
                        f"Plan {config.plan_name!r}: tier {tier_name!r} "
                        f"has a linear early-retire reduction rule "
                        f"without an 'nra' field. Every linear rule "
                        f"must declare its NRA."
                    )
                nra = rule["nra"]
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
