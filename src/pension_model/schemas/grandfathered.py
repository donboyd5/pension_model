"""Schema for the grandfathered-rule predicate used by some tier defs.

A tier with ``assignment: "grandfathered_rule"`` matches a member when the
member would have satisfied a fixed rule at a historical cutoff date —
for example, "age 50 at end of 2005" or "rule of 70 at end of 2005". This
is distinct from the entry-year window other tiers use; entry year alone
isn't enough to identify the grandfathered cohort.
"""

from __future__ import annotations

import numpy as np
from pydantic import model_validator

from pension_model.schemas.base import StrictModel


class GrandfatheredCondition(StrictModel):
    """One alternative inside a grandfathered-rule predicate.

    Each condition stands alone — the parent :class:`GrandfatheredParams`
    OR-combines its conditions. Today's plans use exactly one of the
    three fields per condition; the validator enforces that.
    """

    min_age_at_cutoff: int | None = None
    rule_of_at_cutoff: int | None = None
    min_yos_at_cutoff: int | None = None

    @model_validator(mode="after")
    def _check_exactly_one_field(self):
        present = [
            self.min_age_at_cutoff is not None,
            self.rule_of_at_cutoff is not None,
            self.min_yos_at_cutoff is not None,
        ]
        if sum(present) != 1:
            raise ValueError(
                "GrandfatheredCondition must declare exactly one of "
                "min_age_at_cutoff, rule_of_at_cutoff, min_yos_at_cutoff"
            )
        return self


class GrandfatheredParams(StrictModel):
    """The full grandfathered-rule predicate for a tier.

    A member is grandfathered when, evaluated at ``cutoff_year`` using
    the member's age + yos as of that cutoff, **any** of the
    ``conditions`` matches.

    Members hired after ``cutoff_year`` are never grandfathered (their
    yos at cutoff would be negative).
    """

    cutoff_year: int
    conditions: list[GrandfatheredCondition]

    def matches(self, entry_year: int, entry_age: int) -> bool:
        """Scalar predicate. True iff the member is grandfathered."""
        if entry_year > self.cutoff_year:
            return False
        yos_at_cutoff = min(self.cutoff_year - entry_year, 70)
        age_at_cutoff = entry_age + yos_at_cutoff
        for cond in self.conditions:
            if cond.min_age_at_cutoff is not None and age_at_cutoff >= cond.min_age_at_cutoff:
                return True
            if (
                cond.rule_of_at_cutoff is not None
                and (age_at_cutoff + yos_at_cutoff) >= cond.rule_of_at_cutoff
            ):
                return True
            if cond.min_yos_at_cutoff is not None and yos_at_cutoff >= cond.min_yos_at_cutoff:
                return True
        return False

    def matches_vec(self, entry_year: np.ndarray, entry_age: np.ndarray) -> np.ndarray:
        """Vectorized predicate. Returns bool array."""
        in_range = entry_year <= self.cutoff_year
        yos_at_cutoff = np.minimum(self.cutoff_year - entry_year, 70)
        age_at_cutoff = entry_age + yos_at_cutoff

        result = np.zeros(len(entry_year), dtype=bool)
        for cond in self.conditions:
            if cond.min_age_at_cutoff is not None:
                result |= in_range & (age_at_cutoff >= cond.min_age_at_cutoff)
            if cond.rule_of_at_cutoff is not None:
                result |= in_range & ((age_at_cutoff + yos_at_cutoff) >= cond.rule_of_at_cutoff)
            if cond.min_yos_at_cutoff is not None:
                result |= in_range & (yos_at_cutoff >= cond.min_yos_at_cutoff)
        return result
