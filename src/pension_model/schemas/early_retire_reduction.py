"""Schema for early-retire-reduction (ERR) tier blocks.

Two structurally distinct shapes appear in plan configs today:

* **Flat**: a single ``rate_per_year`` plus a per-class ``nra`` map.
  Used by FRS. The reduction at distribution age ``a`` for a member of
  class ``c`` is ``1 - rate_per_year * (nra[c] - a)``.

* **Rule-list**: a list of ``rules``, each with its own
  ``condition`` predicate and a ``formula`` of either ``linear``
  (rate_per_year + nra) or ``table`` (lookup in a CSV reduce table).
  First-match wins. Used by TXTRS.

The two shapes don't share fields, so we model them as one combined
:class:`EarlyRetireReduction` with both shapes' fields optional, and a
validator that enforces exactly-one-shape at parse time. Consumers
read ``err.rate_per_year`` (flat) or ``err.rules`` (rule-list); both
attributes always exist.
"""

from __future__ import annotations

from typing import Literal, Optional

import numpy as np
from pydantic import Field, model_validator

from pension_model.schemas.base import StrictModel


class ReduceCondition(StrictModel):
    """Predicate inside one rule of a rule-list early-retire reduction.

    Like :class:`pension_model.schemas.conditions.Condition` it has
    ``min_age`` / ``min_yos`` / ``rule_of``, but adds two
    ERR-specific fields:

    * ``grandfathered`` — when True, the rule applies only to members
      whose tier name contains ``"grandfathered"``. (A simple way to
      gate one rule on tier identity without threading the tier in
      separately.)
    * ``or_`` (JSON: ``or``) — sub-conditions OR-combined. The parent
      condition's other fields still must match in addition to one of
      the ``or`` alternatives.

    An empty condition (no fields set) is "always true" — used as the
    catch-all final rule in plan configs.
    """

    model_config = StrictModel.model_config | {"populate_by_name": True}

    min_age: Optional[int] = None
    min_yos: Optional[int] = None
    rule_of: Optional[int] = None
    grandfathered: Optional[bool] = None
    or_: Optional[list["ReduceCondition"]] = Field(default=None, alias="or")

    def matches(self, dist_age: int, yos: int, tier_name: str) -> bool:
        """Scalar predicate evaluation."""
        if self.min_age is not None and dist_age < self.min_age:
            return False
        if self.min_yos is not None and yos < self.min_yos:
            return False
        if self.rule_of is not None and (dist_age + yos) < self.rule_of:
            return False
        if self.grandfathered and "grandfathered" not in tier_name:
            return False
        if self.or_ is not None:
            return any(sub.matches(dist_age, yos, tier_name) for sub in self.or_)
        return True

    def matches_vec(
        self, dist_age: np.ndarray, yos: np.ndarray, tier_name: str
    ) -> np.ndarray:
        """Vectorized predicate evaluation."""
        mask = np.ones(len(dist_age), dtype=bool)
        if self.min_age is not None:
            mask &= dist_age >= self.min_age
        if self.min_yos is not None:
            mask &= yos >= self.min_yos
        if self.rule_of is not None:
            mask &= (dist_age + yos) >= self.rule_of
        if self.grandfathered and "grandfathered" not in tier_name:
            mask &= False
        if self.or_ is not None:
            or_mask = np.zeros(len(dist_age), dtype=bool)
            for sub in self.or_:
                or_mask |= sub.matches_vec(dist_age, yos, tier_name)
            mask &= or_mask
        return mask


class EarlyRetireRule(StrictModel):
    """One rule in a rule-list early-retire reduction.

    Every rule has a ``condition`` (possibly empty for a catch-all)
    and a ``formula``. ``formula="linear"`` requires ``rate_per_year``
    and ``nra``; ``formula="table"`` requires ``table_key`` (looked up
    against the plan's reduce-tables CSVs at runtime).
    """

    condition: ReduceCondition = ReduceCondition()
    formula: Literal["linear", "table"] = "linear"
    rate_per_year: Optional[float] = None
    nra: Optional[int] = None
    table_key: Optional[str] = None

    @model_validator(mode="after")
    def _check_formula_fields(self):
        if self.formula == "linear":
            if self.rate_per_year is None or self.nra is None:
                raise ValueError(
                    "EarlyRetireRule with formula='linear' requires "
                    "both rate_per_year and nra"
                )
        elif self.formula == "table":
            if not self.table_key:
                raise ValueError(
                    "EarlyRetireRule with formula='table' requires "
                    "table_key"
                )
        return self


class EarlyRetireReduction(StrictModel):
    """Tier-level early-retire reduction spec.

    Either flat-shape (``rate_per_year`` + ``nra``) **or** rule-list
    (``rules``). The validator enforces exactly one shape — both
    populated, or neither, raises.
    """

    rate_per_year: Optional[float] = None
    nra: Optional[dict[str, int]] = None
    rules: Optional[list[EarlyRetireRule]] = None

    @model_validator(mode="after")
    def _check_exactly_one_shape(self):
        flat_present = self.rate_per_year is not None or self.nra is not None
        rules_present = self.rules is not None
        if flat_present and rules_present:
            raise ValueError(
                "EarlyRetireReduction cannot mix flat shape "
                "(rate_per_year+nra) with rule-list shape (rules)"
            )
        if not flat_present and not rules_present:
            raise ValueError(
                "EarlyRetireReduction must declare either flat shape "
                "(rate_per_year+nra) or rule-list shape (rules)"
            )
        if flat_present and (self.rate_per_year is None or self.nra is None):
            raise ValueError(
                "EarlyRetireReduction flat shape requires both "
                "rate_per_year and nra"
            )
        return self

    @property
    def is_flat(self) -> bool:
        return self.rules is None

    def lookup_nra(self, class_name: str, plan_name: str, tier_name: str) -> int:
        """Resolve the NRA for one class under flat-shape ERR.

        Falls back to ``nra["default"]`` when ``class_name`` is not
        listed. Raises with a clear message when neither is present.
        Only valid when ``is_flat`` is True.
        """
        if self.nra is None:
            raise ValueError(
                f"Plan {plan_name!r}: tier {tier_name!r} has no "
                f"flat-shape NRA map (rule-list ERR doesn't use this)"
            )
        if class_name in self.nra:
            return self.nra[class_name]
        if "default" in self.nra:
            return self.nra["default"]
        raise ValueError(
            f"Plan {plan_name!r}: NRA map for tier "
            f"{tier_name!r} has no entry for class {class_name!r} "
            f"and no 'default' fallback. Add either an explicit "
            f"per-class NRA or a 'default' key to "
            f"early_retire_reduction.nra."
        )


ReduceCondition.model_rebuild()
