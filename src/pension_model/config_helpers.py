"""Config-derived helper functions used outside the main loader/schema module."""

from typing import Tuple

from pension_model.config_schema import PlanConfig


def _matches_condition(
    cond: dict,
    age: int,
    yos: int,
    entry_year: int = 0,
    entry_age: int = 0,
) -> bool:
    """Check if a single condition dict is satisfied."""
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
    """Check if any rule in the list matches."""
    for rule in rules:
        if _matches_condition(rule, age, yos, entry_year, entry_age):
            return True
    return False


def _resolve_tier_def(tier_name: str, tier_defs: tuple) -> dict:
    """Find a tier def by name."""
    for tier_def in tier_defs:
        if tier_def["name"] == tier_name:
            return tier_def
    raise ValueError(f"Unknown tier: {tier_name}")


def _get_eligibility(tier_def: dict, group: str, all_tier_defs: tuple) -> dict:
    """Get eligibility rules for a tier+group, following same_as references."""
    current = tier_def
    seen = set()
    while "eligibility_same_as" in current:
        ref = current["eligibility_same_as"]
        if ref in seen:
            raise ValueError(f"Circular eligibility_same_as: {ref}")
        seen.add(ref)
        current = _resolve_tier_def(ref, all_tier_defs)

    eligibility = current["eligibility"]
    return eligibility.get(group, eligibility.get("default", {}))


def extract_normal_retirement_params(
    config: PlanConfig,
    tier_name: str,
    class_name: str,
) -> tuple:
    """Extract NRA, min vesting YOS, and YOS-only threshold from tier eligibility."""
    tier_base = tier_name
    for suffix in ("_norm", "_early", "_vested", "_non_vested", "_reduced"):
        if tier_base.endswith(suffix):
            tier_base = tier_base[:-len(suffix)]
            break

    tier_def = _resolve_tier_def(tier_base, config.tier_defs)
    group = config.class_group(class_name)
    eligibility = _get_eligibility(tier_def, group, config.tier_defs)
    normal_rules = eligibility.get("normal", [])

    nra = None
    nra_yos = None
    yos_threshold = None

    for rule in normal_rules:
        has_age = "min_age" in rule
        has_yos = "min_yos" in rule
        has_rule_of = "rule_of" in rule

        if has_yos and not has_age and not has_rule_of:
            if yos_threshold is None or rule["min_yos"] < yos_threshold:
                yos_threshold = rule["min_yos"]
        elif has_age and has_yos and not has_rule_of:
            if nra_yos is None or rule["min_yos"] < nra_yos:
                nra = rule["min_age"]
                nra_yos = rule["min_yos"]

    if nra_yos is None:
        nra_yos = eligibility.get("vesting_yos", 5)

    return nra, nra_yos, yos_threshold


def resolve_cola_scalar(
    config: PlanConfig,
    tier_name: str,
    entry_year: int,
    yos: int,
) -> float:
    """Scalar COLA lookup mirroring the vectorized resolver."""
    tier_base = tier_name
    for suffix in ("_norm", "_early", "_vested", "_non_vested", "_reduced"):
        if tier_base.endswith(suffix):
            tier_base = tier_base[:-len(suffix)]
            break

    tier_def = _resolve_tier_def(tier_base, config.tier_defs)
    cola_key = tier_def["cola_key"]
    raw_cola = config.cola.get(cola_key, 0.0)
    cola_cutoff = config.cola_proration_cutoff_year

    should_prorate = (
        tier_def.get("prorate_cola", False)
        and not config.cola.get(cola_key + "_constant", False)
        and cola_cutoff is not None
        and raw_cola > 0
    )

    if should_prorate and yos > 0:
        yos_b4 = min(max(cola_cutoff - entry_year, 0), yos)
        return raw_cola * yos_b4 / yos
    return raw_cola


def get_sep_type(tier: str) -> str:
    """Determine separation type from tier string."""
    if any(part in tier for part in ("early", "norm", "reduced")):
        return "retire"
    if "non_vested" in tier:
        return "non_vested"
    if "vested" in tier:
        return "vested"
    return "non_vested"


def get_plan_design_ratios(config: PlanConfig, class_name: str) -> Tuple[float, float, float]:
    """Return ``(before, after, new)`` DB plan-design ratios."""
    group = config.class_group(class_name)
    ratios = config.plan_design_defs.get(group, config.plan_design_defs.get("default", {}))
    before = ratios.get("before_2018", ratios.get("before_new_year", 1.0))
    after = ratios.get("after_2018", ratios.get("after_new_year", before))
    new = ratios.get("new", ratios.get("new_db", 1.0))
    return before, after, new
