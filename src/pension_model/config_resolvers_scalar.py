"""Scalar config-derived resolvers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pension_model.config_resolver_common import _lookup_reduce_table

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
    for tier in config.tier_defs:
        if tier.assignment == "grandfathered_rule":
            effective_entry_age = entry_age if entry_age > 0 else (age - yos)
            assert tier.grandfathered_params is not None
            if tier.grandfathered_params.matches(entry_year, effective_entry_age):
                matched_tier = tier
                break
        elif tier.entry_year_in_window(entry_year, config.new_year):
            if tier.not_grandfathered:
                gf_tier = next(
                    (t for t in config.tier_defs if t.assignment == "grandfathered_rule"),
                    None,
                )
                if gf_tier is not None:
                    effective_entry_age = entry_age if entry_age > 0 else (age - yos)
                    assert gf_tier.grandfathered_params is not None
                    if gf_tier.grandfathered_params.matches(entry_year, effective_entry_age):
                        continue
            matched_tier = tier
            break

    if matched_tier is None:
        matched_tier = config.tier_defs[-1]

    tier_name = matched_tier.name
    eligibility = matched_tier.resolve_eligibility(group, config.tier_defs)

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

    tier = next((t for t in config.tier_defs if t.name == tier_name), None)
    if tier is None:
        return float("nan")

    reduction = tier.resolve_early_retire_reduction(config.tier_defs)
    if reduction is None:
        return float("nan")

    if reduction.is_flat:
        nra = reduction.lookup_nra(class_name, config.plan_name, tier_name)
        assert reduction.rate_per_year is not None
        return 1.0 - reduction.rate_per_year * (nra - dist_age)

    assert reduction.rules is not None
    for rule in reduction.rules:
        if not rule.condition.matches(dist_age, yos, tier_name):
            continue
        if rule.formula == "linear":
            assert rule.rate_per_year is not None and rule.nra is not None
            return max(0.0, 1.0 - rule.rate_per_year * (rule.nra - dist_age))
        if rule.formula == "table":
            assert rule.table_key is not None
            if config.reduce_tables and rule.table_key in config.reduce_tables:
                return _lookup_reduce_table(
                    config.reduce_tables[rule.table_key],
                    rule.table_key,
                    dist_age,
                    yos,
                )
            raise ValueError(
                f"early-retire reduction rule references table_key={rule.table_key!r} "
                f"but no matching reduction table is loaded for plan {config.plan_name!r}. "
                f"Provide the table CSV under the plan's data directory."
            )
    return float("nan")
