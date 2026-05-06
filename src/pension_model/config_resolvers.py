"""Stable public resolver API."""

from pension_model.config_schema import EARLY, NON_VESTED, NORM, VESTED
from pension_model.config_resolvers_scalar import (
    get_ben_mult,
    get_reduce_factor,
    get_tier,
)
from pension_model.config_resolvers_vectorized import (
    resolve_ben_mult_vec,
    resolve_cola_vec,
    resolve_reduce_factor_vec,
    resolve_tiers_vec,
    resolve_tiers_vec_str,
)


__all__ = [
    "EARLY",
    "NON_VESTED",
    "NORM",
    "VESTED",
    "get_ben_mult",
    "get_reduce_factor",
    "get_tier",
    "resolve_ben_mult_vec",
    "resolve_cola_vec",
    "resolve_reduce_factor_vec",
    "resolve_tiers_vec",
    "resolve_tiers_vec_str",
]
