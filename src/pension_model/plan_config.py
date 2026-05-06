"""Stable public config API.

The implementation now lives in smaller topic modules, but this file remains
the import surface for callers and tests that still do
``from pension_model.plan_config import ...``.
"""

from pension_model.config_helpers import (
    get_plan_design_ratios,
)
from pension_model.config_loading import (
    discover_plans,
    load_plan_config,
    load_plan_config_by_name,
)
from pension_model.config_resolvers import (
    get_ben_mult,
    get_reduce_factor,
    get_tier,
    resolve_ben_mult_vec,
    resolve_cola_vec,
    resolve_reduce_factor_vec,
    resolve_tiers_vec,
)
from pension_model.config_schema import EARLY, NON_VESTED, NORM, VESTED, PlanConfig


__all__ = [
    "EARLY",
    "NON_VESTED",
    "NORM",
    "PlanConfig",
    "VESTED",
    "discover_plans",
    "get_ben_mult",
    "get_plan_design_ratios",
    "get_reduce_factor",
    "get_tier",
    "load_plan_config",
    "load_plan_config_by_name",
    "resolve_ben_mult_vec",
    "resolve_cola_vec",
    "resolve_reduce_factor_vec",
    "resolve_tiers_vec",
]
