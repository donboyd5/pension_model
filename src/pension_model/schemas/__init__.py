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
from pension_model.schemas.benefit_multipliers import (
    BenefitMultipliers,
    ClassMultipliers,
    FlatBeforeYear,
    GradedRule,
    MultiplierRules,
)
from pension_model.schemas.calibration import Calibration, ClassCalibration
from pension_model.schemas.conditions import Condition
from pension_model.schemas.data_spec import DataSpec
from pension_model.schemas.decrements import Decrements
from pension_model.schemas.early_retire_reduction import (
    EarlyRetireReduction,
    EarlyRetireRule,
    ReduceCondition,
)
from pension_model.schemas.eligibility import EligibilitySpec
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
from pension_model.schemas.grandfathered import (
    GrandfatheredCondition,
    GrandfatheredParams,
)
from pension_model.schemas.modeling import AgeGroup, Modeling
from pension_model.schemas.mortality import MortalitySpec
from pension_model.schemas.plan_design import PlanDesign, PlanDesignRatios
from pension_model.schemas.ranges import Ranges
from pension_model.schemas.term_vested import TermVested
from pension_model.schemas.tier import Tier, validate_tier_cross_references
from pension_model.schemas.valuation_inputs import ClassData, ValuationInputs


__all__ = [
    "AgeGroup",
    "AvaSmoothing",
    "Benefit",
    "BenefitMultipliers",
    "Calibration",
    "CashBalance",
    "ClassCalibration",
    "ClassData",
    "ClassMultipliers",
    "Cola",
    "Condition",
    "CorridorAvaSmoothing",
    "DataSpec",
    "DcSpec",
    "Decrements",
    "EarlyRetireReduction",
    "EarlyRetireRule",
    "Economic",
    "EligibilitySpec",
    "FlatBeforeYear",
    "Funding",
    "GainLossAvaSmoothing",
    "GradedRule",
    "GrandfatheredCondition",
    "GrandfatheredParams",
    "LegDef",
    "Modeling",
    "MortalitySpec",
    "MultiplierRules",
    "PlanDesign",
    "PlanDesignRatios",
    "RampSpec",
    "Ranges",
    "RateComponentSpec",
    "RateScheduleEntry",
    "ReduceCondition",
    "StatutoryRates",
    "StrictModel",
    "TermVested",
    "Tier",
    "ValuationInputs",
    "validate_tier_cross_references",
]
