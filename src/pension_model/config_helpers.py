"""Config-derived helper functions used outside the main loader/schema module."""

from pension_model.config_schema import PlanConfig


def get_plan_design_ratios(config: PlanConfig, class_name: str) -> tuple[float, float, float]:
    """Return ``(before, after, new)`` DB plan-design ratios."""
    group = config.class_group(class_name)
    ratios = config.plan_design_defs.get(group, config.plan_design_defs.get("default", {}))
    before = ratios.get("before_cutoff", 1.0)
    after = ratios.get("after_cutoff", before)
    new = ratios.get("new", ratios.get("new_db", 1.0))
    return before, after, new
