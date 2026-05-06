"""Pydantic models for plan_config.json sections.

Conventions:

* Every model inherits from :class:`StrictModel` (``extra=forbid``,
  ``frozen``). Strict on extras catches typos in plan_config.json at
  load time; freezing matches the project-wide "configs are
  immutable" rule.
* Defaults declared in the schema. Cross-field defaulting (e.g.
  ``dr_old`` defaulting to ``dr_current``) via
  ``model_validator(mode="after")``.
* Computed/derived values via ``@property`` on the model class.
* Validators raise ``ValueError`` with a clear message naming the
  field/plan when something doesn't add up.

Migration is incremental — not every plan_config section has a model
yet. See ``scratch/pydantic_migration_plan.md`` for the order.
"""

from pension_model.schemas.base import StrictModel
from pension_model.schemas.benefit import (
    Benefit,
    CashBalance,
    Cola,
    DcSpec,
)
from pension_model.schemas.decrements import Decrements
from pension_model.schemas.economic import Economic
from pension_model.schemas.funding import (
    AvaSmoothing,
    CorridorAvaSmoothing,
    Funding,
    GainLossAvaSmoothing,
    LegDef,
    RampSpec,
    RateComponentSpec,
    RateScheduleEntry,
    StatutoryRates,
)
from pension_model.schemas.modeling import AgeGroup, Modeling
from pension_model.schemas.ranges import Ranges


__all__ = [
    "AgeGroup",
    "AvaSmoothing",
    "Benefit",
    "CashBalance",
    "Cola",
    "CorridorAvaSmoothing",
    "DcSpec",
    "Decrements",
    "Economic",
    "Funding",
    "GainLossAvaSmoothing",
    "LegDef",
    "Modeling",
    "RampSpec",
    "Ranges",
    "RateComponentSpec",
    "RateScheduleEntry",
    "StatutoryRates",
    "StrictModel",
]
