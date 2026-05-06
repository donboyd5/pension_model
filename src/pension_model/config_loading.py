"""Plan config loading and discovery helpers.

Keeps file I/O, scenario merging, and plan auto-discovery separate from the
core ``PlanConfig`` schema and rule-resolution logic in ``plan_config.py``.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from pension_model.config_schema import PlanConfig
from pension_model.schemas import (
    Benefit,
    Calibration,
    ClassCalibration,
    Decrements,
    Economic,
    Funding,
    Modeling,
    PlanDesign,
    Ranges,
    ValuationInputs,
)


log = logging.getLogger(__name__)


def _deep_merge(base: dict, overrides: dict) -> dict:
    """Recursively merge overrides into base dict (returns a new dict)."""
    result = dict(base)
    for key, val in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


def _build_class_to_group(raw: dict) -> Dict[str, str]:
    """Build class-to-group lookup from ``class_groups`` config."""
    class_to_group: Dict[str, str] = {}
    for group_name, members in raw.get("class_groups", {}).items():
        for class_name in members:
            class_to_group[class_name] = group_name
    return class_to_group


def _load_calibration_data(
    calibration_path: Optional[Path],
    *,
    skip_class_calibration: bool,
) -> tuple[Dict[str, ClassCalibration], Optional[float]]:
    """Load calibration payload from JSON when available.

    Returns:
        Tuple of ``(per_class_calibration, global_cal_factor_override)``.
        The per-class dict is keyed by class name, with each value
        a typed :class:`ClassCalibration`.
    """
    if calibration_path is None or not calibration_path.exists():
        return {}, None

    with open(calibration_path) as f:
        cal_raw = json.load(f)

    cal_model = Calibration.model_validate(cal_raw)
    classes = {} if skip_class_calibration else cal_model.classes
    return dict(classes), cal_model.cal_factor


def _build_tier_metadata(
    tier_defs_raw: list[dict],
    *,
    fas_default: int,
) -> tuple[
    dict[str, int],
    tuple[str, ...],
    tuple[str, ...],
    tuple[int, ...],
    tuple[str, ...],
    tuple[str, ...],
]:
    """Build tier lookup tables cached on ``PlanConfig``."""
    tier_name_to_id = {td["name"]: i for i, td in enumerate(tier_defs_raw)}
    tier_id_to_name = tuple(td["name"] for td in tier_defs_raw)
    tier_id_to_cola_key = tuple(td["cola_key"] for td in tier_defs_raw)
    tier_id_to_fas_years = tuple(td.get("fas_years", fas_default) for td in tier_defs_raw)
    tier_id_to_dr_key = tuple(
        td.get("discount_rate_key", "dr_current") for td in tier_defs_raw
    )
    # Default: each tier maps to a rate set with its own name. Plans
    # whose tier names don't match any rate set in the CSV must declare
    # this explicitly (e.g., FRS tier_2 → "2011_or_later"). The set
    # name is era-descriptive, not tier-named, so renaming a tier
    # never breaks another tier's reference.
    tier_id_to_retire_rate_set = tuple(
        td.get("retirement_rate_set", td["name"]) for td in tier_defs_raw
    )
    return (
        tier_name_to_id,
        tier_id_to_name,
        tier_id_to_cola_key,
        tier_id_to_fas_years,
        tier_id_to_dr_key,
        tier_id_to_retire_rate_set,
    )


def _build_economic_model(
    eco_raw: dict,
    baseline_dr_current: float,
    baseline_model_return: float,
) -> Economic:
    """Validate and build the Economic schema model.

    The two ``baseline_*`` fields aren't in the raw economic dict —
    they're snapshots from before any scenario merge, computed by the
    loader and supplied alongside.
    """
    return Economic.model_validate({
        **eco_raw,
        "baseline_dr_current": baseline_dr_current,
        "baseline_model_return": baseline_model_return,
    })


def _build_funding_model(fun_raw: dict, eco_raw: dict) -> Funding:
    """Validate and build the Funding schema model.

    Pre-fills ``amo_pay_growth`` from ``economic.payroll_growth`` if
    the funding block omits it — preserves the pre-pydantic loader's
    defensive default. All other required fields must be declared
    explicitly (the schema enforces).
    """
    fun_with_defaults = dict(fun_raw)
    fun_with_defaults.setdefault("amo_pay_growth", eco_raw["payroll_growth"])
    return Funding.model_validate(fun_with_defaults)


def _build_decrements_model(raw: dict, *, plan_name: str) -> Decrements:
    """Validate and build the Decrements schema model.

    Raises a clear ``KeyError`` if the required ``decrements`` block
    is missing from plan_config.json — preserves the same error
    surface as the previous ``decrements_method`` runtime check.
    """
    decr = raw.get("decrements")
    if not decr:
        raise KeyError(
            f"Plan {plan_name!r}: required field 'decrements' is "
            f"missing from plan_config.json. Set 'decrements.method' "
            f"to 'yos_only' (FRS-style) or 'years_from_nr' "
            f"(TXTRS-style) — see an existing plan's plan_config.json "
            f"for an example."
        )
    return Decrements.model_validate(decr)


def load_plan_config(
    config_path: Path,
    calibration_path: Optional[Path] = None,
    scenario_path: Optional[Path] = None,
    skip_class_calibration: bool = False,
) -> PlanConfig:
    """Load a PlanConfig from a JSON file."""
    with open(config_path) as f:
        raw = json.load(f)

    baseline_dr_current = raw["economic"]["dr_current"]
    baseline_model_return = raw["economic"].get(
        "model_return", baseline_dr_current
    )

    scenario_name = None
    if scenario_path is not None:
        with open(scenario_path) as f:
            scenario = json.load(f)
        scenario_name = scenario.get("name", scenario_path.stem)
        raw = _deep_merge(raw, scenario.get("overrides", {}))

    if scenario_name:
        raw["_scenario_name"] = scenario_name

    eco = raw["economic"]
    ben = raw["benefit"]
    fun = raw["funding"]
    rng = raw["ranges"]

    tier_defs_raw = raw.get("tiers", [])
    class_to_group = _build_class_to_group(raw)
    calibration, cal_factor_override = _load_calibration_data(
        calibration_path,
        skip_class_calibration=skip_class_calibration,
    )
    if cal_factor_override is not None:
        ben = dict(ben)
        ben["cal_factor"] = cal_factor_override

    (
        tier_name_to_id,
        tier_id_to_name,
        tier_id_to_cola_key,
        tier_id_to_fas_years,
        tier_id_to_dr_key,
        tier_id_to_retire_rate_set,
    ) = _build_tier_metadata(
        tier_defs_raw,
        fas_default=ben["fas_years_default"],
    )

    # Parse typed schemas. ``baseline_*`` fields on Economic are
    # populated from the pre-scenario raw config so scenarios don't
    # disturb the term-vested cashflow scaling.
    economic_model = _build_economic_model(eco, baseline_dr_current, baseline_model_return)
    ranges_model = Ranges.model_validate(rng)
    decrements_model = _build_decrements_model(raw, plan_name=raw["plan_name"])
    modeling_model = Modeling.model_validate(raw.get("modeling", {}))
    funding_model = _build_funding_model(fun, eco)
    benefit_model = Benefit.model_validate(ben)
    plan_design_model = PlanDesign.model_validate(raw.get("plan_design", {}))
    valuation_models = {
        cn: ValuationInputs.model_validate(v)
        for cn, v in raw.get("valuation_inputs", {}).items()
    }

    config = PlanConfig(
        plan_name=raw["plan_name"],
        plan_description=raw.get("plan_description", ""),
        raw=raw,
        classes=tuple(raw["classes"]),
        class_groups=raw.get("class_groups", {}),
        tier_defs=tuple(raw.get("tiers", [])),
        benefit_mult_defs=raw.get("benefit_multipliers", {}),
        plan_design=plan_design_model,
        valuation_inputs=valuation_models,
        economic=economic_model,
        ranges=ranges_model,
        decrements=decrements_model,
        modeling=modeling_model,
        funding=funding_model,
        benefit=benefit_model,
        calibration=calibration,
        _class_to_group=class_to_group,
        _tier_name_to_id=tier_name_to_id,
        _tier_id_to_name=tier_id_to_name,
        _tier_id_to_cola_key=tier_id_to_cola_key,
        _tier_id_to_fas_years=tier_id_to_fas_years,
        _tier_id_to_dr_key=tier_id_to_dr_key,
        _tier_id_to_retire_rate_set=tier_id_to_retire_rate_set,
    )

    # Fatal: legs must be non-overlapping and cover the full
    # entry-year range. Raises ValueError on misconfiguration.
    from pension_model.config_validation import validate_funding_legs
    validate_funding_legs(config)

    for warning in config.validate():
        log.info("[%s config] %s", config.plan_name, warning)

    return config


def discover_plans(plans_dir: Optional[Path] = None) -> dict[str, Path]:
    """Return {plan_name: plan_config.json path} for discovered plans."""
    if plans_dir is None:
        plans_dir = Path(__file__).parents[2] / "plans"
    plans: dict[str, Path] = {}
    if not plans_dir.is_dir():
        return plans
    for entry in sorted(plans_dir.iterdir()):
        if not entry.is_dir():
            continue
        cfg = entry / "config" / "plan_config.json"
        if cfg.exists():
            plans[entry.name] = cfg
    return plans


def load_plan_config_by_name(
    plan_name: str,
    calibration_path: Optional[Path] = None,
) -> PlanConfig:
    """Load a plan config by plan directory name."""
    plans = discover_plans()
    if plan_name not in plans:
        raise ValueError(f"Unknown plan {plan_name!r}. Available: {sorted(plans)}")
    config_path = plans[plan_name]
    if calibration_path is None:
        cal_path = config_path.parent / "calibration.json"
        cal_path = cal_path if cal_path.exists() else None
    else:
        cal_path = calibration_path
    return load_plan_config(config_path, cal_path)
