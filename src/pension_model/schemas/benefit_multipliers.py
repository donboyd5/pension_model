"""Schema for the ``benefit_multipliers`` block of plan_config.json.

Structure:

* Top level: keyed by class name (``regular``, ``special``, ``all``, …).
* Per-class: keyed by tier name (``tier_1``, ``tier_2``, …) or
  ``all_tiers`` (single rules block applied to every tier of that
  class). Plans can also declare a ``<tier_name>_same_as`` key whose
  value is a string naming another tier — the alias resolves at
  lookup time.
* Per-tier (or ``all_tiers``): a :class:`MultiplierRules` block with
  one of the supported rule shapes (flat, graded, etc.).

Tier and class names are dynamic by plan, so ``BenefitMultipliers``
and ``ClassMultipliers`` use ``extra="allow"``. A ``model_validator``
promotes the raw extras to typed sub-models at parse time.
"""

from __future__ import annotations

from pydantic import ConfigDict, Field, model_validator

from pension_model.schemas.base import StrictModel
from pension_model.schemas.conditions import Condition


class FlatBeforeYear(StrictModel):
    """Override the flat multiplier with ``mult`` for distribution
    years on or before ``year``."""

    year: int
    mult: float


class GradedRule(StrictModel):
    """One row in a graded multiplier table.

    The rule fires when **any** of the conditions in ``or_`` match
    (logical OR over the list). The corresponding ``mult`` is then
    used as the benefit multiplier.
    """

    or_: list[Condition] = Field(alias="or")
    mult: float

    # The JSON key is ``or`` (a Python keyword); we expose it as
    # ``or_`` on the model. ``populate_by_name`` lets callers also
    # construct via ``GradedRule(or_=...)`` programmatically.
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class MultiplierRules(StrictModel):
    """Multiplier-rules block for one (class, tier) pair.

    Exactly one of ``flat`` or ``graded`` is the primary rule
    (validated). ``flat_before_year`` overrides ``flat`` for early
    years; ``early_fallback`` is used as the multiplier when
    ``status == "early"`` and no graded entry matched.
    """

    flat: float | None = None
    flat_before_year: FlatBeforeYear | None = None
    graded: list[GradedRule] | None = None
    early_fallback: float | None = None

    @model_validator(mode="after")
    def _check_primary_rule(self) -> MultiplierRules:
        if self.flat is None and self.graded is None:
            raise ValueError(
                "MultiplierRules: must declare either 'flat' or 'graded' "
                "as the primary rule. Neither was provided."
            )
        if self.flat is not None and self.graded is not None:
            raise ValueError(
                "MultiplierRules: 'flat' and 'graded' are mutually "
                "exclusive primary rules. Pick one."
            )
        if self.flat_before_year is not None and self.flat is None:
            raise ValueError(
                "MultiplierRules: 'flat_before_year' requires 'flat' to " "be the primary rule."
            )
        return self


# Per-class entry: either typed rules or a string alias (``_same_as``).
_PerClassEntry = MultiplierRules | str


class ClassMultipliers(StrictModel):
    """Per-class benefit-multiplier block.

    Keys are tier names, ``all_tiers``, or ``<tier_name>_same_as``
    strings. Values are :class:`MultiplierRules` (for tier names and
    ``all_tiers``) or a string naming the target tier (for
    ``_same_as`` aliases). ``extra="allow"`` admits the dynamic key
    set; the validator promotes raw entries.
    """

    model_config = ConfigDict(extra="allow", frozen=True)

    @model_validator(mode="after")
    def _promote_entries(self) -> ClassMultipliers:
        if not self.model_extra:
            return self
        promoted = {}
        for key, raw in self.model_extra.items():
            if isinstance(raw, str):
                # ``<tier>_same_as`` alias — keep as string.
                promoted[key] = raw
            elif isinstance(raw, MultiplierRules):
                promoted[key] = raw
            else:
                promoted[key] = MultiplierRules.model_validate(raw)
        object.__setattr__(self, "__pydantic_extra__", promoted)
        return self

    def resolve(self, tier_name: str) -> MultiplierRules | None:
        """Look up the multiplier rules for a tier.

        Resolution order:
          1. ``all_tiers`` if present (single rules block for every tier).
          2. Direct match on ``tier_name``.
          3. ``<tier_name>_same_as`` alias — recurse on the target.

        Returns None if no rules match.
        """
        entries = self.model_extra or {}
        if "all_tiers" in entries:
            return entries["all_tiers"]
        rules = entries.get(tier_name)
        if rules is None:
            alias_key = f"{tier_name}_same_as"
            if alias_key in entries and isinstance(entries[alias_key], str):
                return self.resolve(entries[alias_key])
        return rules


class BenefitMultipliers(StrictModel):
    """Top-level benefit_multipliers block.

    Keys are class names. Values are :class:`ClassMultipliers`
    (admitted as extras and promoted at parse time).
    """

    model_config = ConfigDict(extra="allow", frozen=True)

    @model_validator(mode="after")
    def _promote_classes(self) -> BenefitMultipliers:
        if not self.model_extra:
            return self
        promoted = {}
        for class_name, raw in self.model_extra.items():
            if isinstance(raw, ClassMultipliers):
                promoted[class_name] = raw
            else:
                promoted[class_name] = ClassMultipliers.model_validate(raw)
        object.__setattr__(self, "__pydantic_extra__", promoted)
        return self

    def resolve(self, class_name: str, tier_name: str) -> MultiplierRules | None:
        """Look up multiplier rules for a (class, tier) pair.

        Returns None if the class isn't declared or has no matching
        tier rules.
        """
        class_rules = (self.model_extra or {}).get(class_name)
        if class_rules is None:
            return None
        return class_rules.resolve(tier_name)

    def class_multipliers(self, class_name: str) -> ClassMultipliers | None:
        """Return the typed ClassMultipliers for ``class_name``,
        or None if absent."""
        return (self.model_extra or {}).get(class_name)
