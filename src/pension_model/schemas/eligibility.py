"""Schema for tier eligibility rules (per (tier, group))."""

from __future__ import annotations

import numpy as np
from pydantic import Field

from pension_model.schemas.base import StrictModel
from pension_model.schemas.conditions import Condition


def _any_match_vec(conditions: list[Condition], ages: np.ndarray, yos: np.ndarray) -> np.ndarray:
    """Vectorized OR of per-condition matches. Empty list → all-False."""
    if not conditions:
        return np.zeros(len(ages), dtype=bool)
    mask = conditions[0].matches_vec(ages, yos)
    for c in conditions[1:]:
        mask |= c.matches_vec(ages, yos)
    return mask


class EligibilitySpec(StrictModel):
    """Eligibility rules for one (tier, group) pair.

    The ``normal`` and ``early`` lists are OR-combinations of
    conditions: the member is eligible if **any** condition in the
    list matches. ``vesting_yos`` is the years-of-service threshold
    above which a terminated member is treated as deferred-vested
    (rather than non-vested with refund only).
    """

    normal: list[Condition] = Field(default_factory=list)
    early: list[Condition] = Field(default_factory=list)
    vesting_yos: int

    def matches_normal(self, age: int, yos: int) -> bool:
        """True if any normal-retirement condition matches."""
        return any(c.matches(age, yos) for c in self.normal)

    def matches_early(self, age: int, yos: int) -> bool:
        """True if any early-retirement condition matches."""
        return any(c.matches(age, yos) for c in self.early)

    def matches_normal_vec(
        self, ages: np.ndarray, yos: np.ndarray
    ) -> np.ndarray:
        """Vectorized normal-retirement match. Returns bool array."""
        return _any_match_vec(self.normal, ages, yos)

    def matches_early_vec(
        self, ages: np.ndarray, yos: np.ndarray
    ) -> np.ndarray:
        """Vectorized early-retirement match. Returns bool array."""
        return _any_match_vec(self.early, ages, yos)
