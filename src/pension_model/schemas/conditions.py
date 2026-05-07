"""Shared predicate types used by both eligibility rules and benefit-multiplier
graded tables.

Eligibility and graded multipliers both express "this rule applies when the
member meets these conditions" — same shape, same set of fields. The schema
keeps a single :class:`Condition` model so both consumers can reuse it.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from pension_model.schemas.base import StrictModel


class Condition(StrictModel):
    """A single predicate over (age, yos, entry_year).

    A condition matches a member when **every** declared field is
    satisfied. Missing fields don't constrain anything. Today's
    supported fields:

    * ``min_age`` — member's age >= this.
    * ``min_yos`` — member's years of service >= this.
    * ``rule_of`` — age + yos >= this (the "rule of N" pattern).

    Plans express OR-combinations as a list of conditions inside a
    higher-level container (e.g. ``GradedRule.or_`` or eligibility
    rule lists).

    A condition with no fields set is "always true" — used as a
    catch-all in early-retire-reduction rules. (Today's eligibility
    rules don't use the empty form.)
    """

    min_age: Optional[int] = None
    min_yos: Optional[int] = None
    rule_of: Optional[int] = None

    def matches(self, age: int, yos: int) -> bool:
        """Scalar predicate evaluation. Returns True iff all declared
        fields are satisfied for the given (age, yos)."""
        if self.min_age is not None and age < self.min_age:
            return False
        if self.min_yos is not None and yos < self.min_yos:
            return False
        if self.rule_of is not None and (age + yos) < self.rule_of:
            return False
        return True

    def matches_vec(self, ages: np.ndarray, yos: np.ndarray) -> np.ndarray:
        """Vectorized predicate evaluation. Returns a bool array
        with one entry per (ages[i], yos[i]) pair."""
        mask = np.ones(len(ages), dtype=bool)
        if self.min_age is not None:
            mask &= ages >= self.min_age
        if self.min_yos is not None:
            mask &= yos >= self.min_yos
        if self.rule_of is not None:
            mask &= (ages + yos) >= self.rule_of
        return mask
