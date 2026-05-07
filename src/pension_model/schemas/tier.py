"""Schema for a single tier definition.

A :class:`Tier` composes the per-tier scalars (cola key, FAS years,
discount rate, retirement-rate set, entry-year window) with the larger
sub-models defined in earlier migration PRs:

* :class:`pension_model.schemas.eligibility.EligibilitySpec` —
  per-(tier, group) normal/early/vesting predicates.
* :class:`pension_model.schemas.early_retire_reduction.EarlyRetireReduction` —
  flat or rule-list ERR spec.
* :class:`pension_model.schemas.grandfathered.GrandfatheredParams` —
  for the optional grandfathered-rule assignment.

Plans use ``eligibility_same_as`` and ``early_retire_reduction_same_as``
to share specs between tiers (e.g. FRS tier_3 inherits from tier_2).
The cross-reference resolution helpers walk those chains with cycle
detection. List-level validation (``validate_tier_cross_references``)
ensures every reference targets an existing tier name; called from
the loader so misspelled references fail at parse time.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import numpy as np
from pydantic import model_validator

from pension_model.schemas.base import StrictModel
from pension_model.schemas.early_retire_reduction import EarlyRetireReduction
from pension_model.schemas.eligibility import EligibilitySpec
from pension_model.schemas.grandfathered import GrandfatheredParams


class Tier(StrictModel):
    """One tier in a plan's tiers list.

    See module docstring for the composition story. Field-level
    invariants checked here:

    * Either ``eligibility`` or ``eligibility_same_as`` is set (not
      both, and at least one must be present).
    * Either ``early_retire_reduction`` or
      ``early_retire_reduction_same_as`` is set (same rule).
    * Tiers with ``assignment="grandfathered_rule"`` must declare
      ``grandfathered_params``; non-grandfathered tiers must not.
    """

    name: str
    cola_key: str
    fas_years: int
    retirement_rate_set: str

    discount_rate_key: str = "dr_current"
    prorate_cola: bool = False

    entry_year_min: int | None = None
    entry_year_max: int | None = None
    entry_year_min_param: Literal["new_year"] | None = None
    entry_year_max_param: Literal["new_year"] | None = None

    eligibility: dict[str, EligibilitySpec] | None = None
    eligibility_same_as: str | None = None

    early_retire_reduction: EarlyRetireReduction | None = None
    early_retire_reduction_same_as: str | None = None

    assignment: Literal["grandfathered_rule"] | None = None
    grandfathered_params: GrandfatheredParams | None = None
    not_grandfathered: bool = False

    @model_validator(mode="after")
    def _check_xor_and_assignment(self):
        if self.eligibility is None and self.eligibility_same_as is None:
            raise ValueError(
                f"Tier {self.name!r}: must declare either "
                f"'eligibility' or 'eligibility_same_as'"
            )
        if self.eligibility is not None and self.eligibility_same_as is not None:
            raise ValueError(
                f"Tier {self.name!r}: cannot declare both "
                f"'eligibility' and 'eligibility_same_as'"
            )
        if self.early_retire_reduction is None and self.early_retire_reduction_same_as is None:
            raise ValueError(
                f"Tier {self.name!r}: must declare either "
                f"'early_retire_reduction' or "
                f"'early_retire_reduction_same_as'"
            )
        if (
            self.early_retire_reduction is not None
            and self.early_retire_reduction_same_as is not None
        ):
            raise ValueError(
                f"Tier {self.name!r}: cannot declare both "
                f"'early_retire_reduction' and "
                f"'early_retire_reduction_same_as'"
            )

        if self.assignment == "grandfathered_rule":
            if self.grandfathered_params is None:
                raise ValueError(
                    f"Tier {self.name!r}: assignment='grandfathered_rule' "
                    f"requires grandfathered_params"
                )
        else:
            if self.grandfathered_params is not None:
                raise ValueError(
                    f"Tier {self.name!r}: grandfathered_params is only "
                    f"valid when assignment='grandfathered_rule'"
                )
        return self

    def entry_year_lo(self, new_year: int) -> int | None:
        """Resolved lower bound (inclusive) of this tier's entry-year
        window. ``None`` means unbounded below.
        """
        if self.entry_year_min_param == "new_year":
            return new_year
        return self.entry_year_min

    def entry_year_hi(self, new_year: int) -> int | None:
        """Resolved upper bound (exclusive) of this tier's entry-year
        window. ``None`` means unbounded above.
        """
        if self.entry_year_max_param == "new_year":
            return new_year
        return self.entry_year_max

    def entry_year_in_window(self, entry_year: int, new_year: int) -> bool:
        """True if ``entry_year`` falls in this tier's window.

        Tiers with assignment ``grandfathered_rule`` always return
        False — they're matched by the grandfathered predicate, not
        by entry year.
        """
        if self.assignment == "grandfathered_rule":
            return False
        lo = self.entry_year_lo(new_year)
        hi = self.entry_year_hi(new_year)
        if lo is not None and entry_year < lo:
            return False
        if hi is not None and entry_year >= hi:
            return False
        return True

    def entry_year_in_window_vec(self, entry_year: np.ndarray, new_year: int) -> np.ndarray:
        """Vectorized version of :meth:`entry_year_in_window`."""
        if self.assignment == "grandfathered_rule":
            return np.zeros(len(entry_year), dtype=bool)
        lo = self.entry_year_lo(new_year)
        hi = self.entry_year_hi(new_year)
        mask = np.ones(len(entry_year), dtype=bool)
        if lo is not None:
            mask &= entry_year >= lo
        if hi is not None:
            mask &= entry_year < hi
        return mask

    def resolve_eligibility(
        self,
        group: str,
        all_tiers: Sequence[Tier],
    ) -> EligibilitySpec | None:
        """Resolve this tier's eligibility for ``group``.

        Walks ``eligibility_same_as`` references (cycle-checked), then
        looks up the group, falling back to ``"default"``. Returns
        ``None`` when no matching spec exists — only happens for
        DROP-shaped tiers and similar edge cases.
        """
        current = self
        seen: set[str] = set()
        while current.eligibility_same_as is not None:
            ref = current.eligibility_same_as
            if ref in seen:
                raise ValueError(
                    f"Tier {self.name!r}: circular eligibility_same_as " f"chain at {ref!r}"
                )
            seen.add(ref)
            current = _find_tier(ref, all_tiers, source_field="eligibility_same_as")
        if current.eligibility is None:
            return None
        return current.eligibility.get(group, current.eligibility.get("default"))

    def resolve_early_retire_reduction(
        self,
        all_tiers: Sequence[Tier],
    ) -> EarlyRetireReduction | None:
        """Resolve this tier's early-retire-reduction spec.

        Walks ``early_retire_reduction_same_as`` references
        (cycle-checked). Returns ``None`` only when neither inline
        nor reference resolves to a concrete spec — shouldn't happen
        for valid configs given the field-level XOR validator.
        """
        current = self
        seen: set[str] = set()
        while current.early_retire_reduction_same_as is not None:
            ref = current.early_retire_reduction_same_as
            if ref in seen:
                raise ValueError(
                    f"Tier {self.name!r}: circular "
                    f"early_retire_reduction_same_as chain at {ref!r}"
                )
            seen.add(ref)
            current = _find_tier(ref, all_tiers, source_field="early_retire_reduction_same_as")
        return current.early_retire_reduction


def _find_tier(name: str, tiers: Sequence[Tier], *, source_field: str) -> Tier:
    for t in tiers:
        if t.name == name:
            return t
    raise ValueError(
        f"{source_field}={name!r} does not match any tier name in " f"{[t.name for t in tiers]}"
    )


def validate_tier_cross_references(tiers: Sequence[Tier]) -> None:
    """Eager parse-time check that every ``*_same_as`` reference and
    every ``resolve_*`` call from any tier resolves cleanly.

    Catches misspelled references and cycles at config load, before
    any year-by-year solve touches the tiers. Called once from the
    loader after the typed list is built.
    """
    for t in tiers:
        if t.eligibility_same_as is not None:
            _find_tier(
                t.eligibility_same_as,
                tiers,
                source_field=f"tier {t.name!r} eligibility_same_as",
            )
            t.resolve_eligibility("default", tiers)
        if t.early_retire_reduction_same_as is not None:
            _find_tier(
                t.early_retire_reduction_same_as,
                tiers,
                source_field=f"tier {t.name!r} early_retire_reduction_same_as",
            )
            t.resolve_early_retire_reduction(tiers)
