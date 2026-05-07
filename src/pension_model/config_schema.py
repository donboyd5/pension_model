"""Plan config schema and status constants.

The top-level :class:`PlanConfig` is now a pydantic ``BaseModel``
that composes every section schema. Strict (``extra="forbid"``) is
the rule on sub-models; the top-level uses ``extra="ignore"`` so
plain documentation keys (``*_notes``, ``source_notes``) embedded
in plan_config.json don't fail validation. Required sections —
``economic``, ``ranges``, ``decrements``, ``funding``, ``benefit`` —
are still required, so a typo at the top level surfaces as a
"missing required field" error, not a silent drop.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, model_validator

from pension_model.schemas import (
    Benefit,
    BenefitMultipliers,
    ClassCalibration,
    ClassData,
    DataSpec,
    Decrements,
    Economic,
    Funding,
    Modeling,
    MortalitySpec,
    MultiplierRules,
    PlanDesign,
    PlanDesignRatios,
    Ranges,
    TermVested,
    Tier,
    ValuationInputs,
    validate_tier_cross_references,
)


NON_VESTED = 0
VESTED = 1
EARLY = 2
NORM = 3


class PlanConfig(BaseModel):
    """Top-level plan_config.json model.

    Section sub-models (`economic`, `funding`, etc.) are validated
    strictly. The top level itself ignores unknown keys so that
    embedded documentation (``*_notes``, ``source_notes``,
    ``_scenario_name``) doesn't fail load. ``frozen=True`` keeps
    configs immutable; the few lookup tables computed at load time
    use ``object.__setattr__`` in :func:`build_plan_config_from_raw`.
    """

    model_config = ConfigDict(
        extra="ignore",
        frozen=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    plan_name: str
    plan_description: str = ""

    classes: Tuple[str, ...]
    class_groups: Dict[str, List[str]] = Field(default_factory=dict)

    economic: Economic
    ranges: Ranges
    decrements: Decrements
    modeling: Modeling = Field(default_factory=Modeling)
    funding: Funding
    benefit: Benefit

    valuation_inputs: Dict[str, ValuationInputs] = Field(default_factory=dict)
    plan_design: PlanDesign = Field(default_factory=PlanDesign)
    benefit_mult_defs: BenefitMultipliers = Field(
        default_factory=BenefitMultipliers, alias="benefit_multipliers"
    )
    tier_defs: Tuple[Tier, ...] = Field(default=(), alias="tiers")

    data: DataSpec
    mortality: Optional[MortalitySpec] = None
    term_vested: Optional[TermVested] = None

    salary_growth_col_map: Dict[str, str] = Field(default_factory=dict)
    base_table_map: Dict[str, str] = Field(default_factory=dict)
    design_ratio_group_map: Dict[str, str] = Field(default_factory=dict)

    scenario_name: Optional[str] = Field(default=None, alias="_scenario_name")

    # Populated post-load (calibration is read from a sibling file;
    # reduce_tables and the lookup caches are built during loading).
    calibration: Dict[str, ClassCalibration] = Field(default_factory=dict)
    reduce_tables: Optional[Dict[str, Any]] = None
    class_to_group: Dict[str, str] = Field(default_factory=dict)
    tier_name_to_id: Dict[str, int] = Field(default_factory=dict)
    tier_id_to_name: Tuple[str, ...] = ()
    tier_id_to_cola_key: Tuple[str, ...] = ()
    tier_id_to_fas_years: Tuple[int, ...] = ()
    tier_id_to_dr_key: Tuple[str, ...] = ()
    tier_id_to_retire_rate_set: Tuple[str, ...] = ()

    # ------------------------------------------------------------------
    # Cross-reference validation. tier_defs ``*_same_as`` references
    # must resolve to existing tier names; cycles raise.
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def _validate_tier_cross_refs(self):
        if self.tier_defs:
            validate_tier_cross_references(self.tier_defs)
        return self

    # ------------------------------------------------------------------
    # Delegating accessors to typed-model fields. The typed model is
    # the source of truth; these accessors preserve the legacy
    # ``config.dr_current`` / ``config.start_year`` access pattern.
    # ------------------------------------------------------------------

    @property
    def dr_current(self) -> float:
        return self.economic.dr_current

    @property
    def dr_new(self) -> float:
        return self.economic.dr_new

    @property
    def dr_old(self) -> float:
        return self.economic.dr_old  # type: ignore[return-value]

    @property
    def baseline_dr_current(self) -> float:
        return self.economic.baseline_dr_current

    @property
    def baseline_model_return(self) -> float:
        return self.economic.baseline_model_return

    @property
    def payroll_growth(self) -> float:
        return self.economic.payroll_growth

    @property
    def pop_growth(self) -> float:
        return self.economic.pop_growth

    @property
    def model_return(self) -> float:
        return self.economic.model_return  # type: ignore[return-value]

    @property
    def asset_return_path(self) -> Optional[dict]:
        return self.economic.asset_return_path

    @property
    def min_age(self) -> int:
        return self.ranges.min_age

    @property
    def max_age(self) -> int:
        return self.ranges.max_age

    @property
    def start_year(self) -> int:
        return self.ranges.start_year

    @property
    def new_year(self) -> int:
        return self.ranges.new_year  # type: ignore[return-value]

    @property
    def min_entry_year(self) -> int:
        return self.ranges.min_entry_year

    @property
    def model_period(self) -> int:
        return self.ranges.model_period

    @property
    def max_yos(self) -> int:
        return self.ranges.max_yos

    @property
    def db_ee_cont_rate(self) -> float:
        return self.benefit.db_ee_cont_rate

    @property
    def db_ee_interest_rate(self) -> float:
        return self.benefit.db_ee_interest_rate

    @property
    def cal_factor(self) -> float:
        return self.benefit.cal_factor

    @property
    def retire_refund_ratio(self) -> float:
        return self.benefit.retire_refund_ratio

    @property
    def fas_years_default(self) -> int:
        return self.benefit.fas_years_default

    @property
    def benefit_types(self) -> Tuple[str, ...]:
        return tuple(self.benefit.benefit_types)

    @property
    def cola(self):
        """Typed Cola model. Use ``getattr(cola, key, default)`` for
        per-tier active-rate keys (admitted as ``extra=\"allow\"``).
        """
        return self.benefit.cola

    @property
    def cash_balance(self):
        """Typed CashBalance model, or None if not declared."""
        return self.benefit.cash_balance

    def resolve_data_dir(self) -> Path:
        data_dir_str = self.data.data_dir
        data_dir = Path(data_dir_str)
        if not data_dir.is_absolute():
            project_root = Path(__file__).parents[2]
            data_dir = project_root / data_dir
        return data_dir

    @property
    def entrant_salary_at_start_year(self) -> bool:
        return self.modeling.entrant_salary_at_start_year

    @property
    def use_earliest_retire(self) -> bool:
        return self.modeling.use_earliest_retire

    @property
    def male_mp_forward_shift(self) -> int:
        return self.modeling.male_mp_forward_shift

    @property
    def cola_proration_cutoff_year(self) -> Optional[int]:
        return self.cola.proration_cutoff_year

    @property
    def plan_design_cutoff_year(self) -> Optional[int]:
        return self.plan_design.cutoff_year

    @property
    def mortality_base_table(self) -> str:
        if self.mortality is not None:
            return self.mortality.base_table
        return "general"

    def get_base_table_type(self, class_name: str) -> str:
        return self.base_table_map.get(class_name, "general")

    @property
    def age_groups(self):
        """Optional list of ``AgeGroup`` models (or None if absent)."""
        return self.modeling.age_groups

    @property
    def has_drop(self) -> bool:
        return self.funding.has_drop

    @property
    def drop_reference_class(self) -> Optional[str]:
        return self.funding.drop_reference_class

    @property
    def statutory_rates(self):
        """Typed StatutoryRates model, or None if not declared."""
        return self.funding.statutory_rates

    @property
    def amo_period_current(self) -> Optional[int]:
        return self.funding.amo_period_current

    @property
    def funding_policy(self) -> str:
        return self.funding.policy

    @property
    def contribution_strategy(self) -> str:
        return self.funding.contribution_strategy

    @property
    def amo_method(self) -> str:
        return self.funding.amo_method

    @property
    def amo_period_new(self) -> int:
        return self.funding.amo_period_new

    @property
    def amo_pay_growth(self) -> float:
        return self.funding.amo_pay_growth

    @property
    def funding_lag(self) -> int:
        return self.funding.funding_lag

    @property
    def amo_period_term(self) -> int:
        return self.funding.amo_period_term

    @property
    def amo_term_growth(self) -> float:
        return self.funding.amo_term_growth

    @property
    def ava_smoothing(self):
        """Typed AVA smoothing spec (CorridorAvaSmoothing or
        GainLossAvaSmoothing).
        """
        return self.funding.ava_smoothing

    @property
    def funding_legs(self) -> Tuple[Tuple[str, Optional[int], Optional[int]], ...]:
        """Resolved funding legs as ``((name, lo, hi), ...)``.

        ``lo`` is inclusive, ``hi`` is exclusive — same convention as
        the tier resolver (``entry_year_min`` / ``entry_year_max``).
        ``entry_year_min_param`` / ``entry_year_max_param`` strings of
        ``"new_year"`` resolve to ``self.new_year``.
        """
        resolved = []
        for leg in self.funding.legs:
            lo = leg.entry_year_min
            if leg.entry_year_min_param == "new_year":
                lo = self.new_year
            hi = leg.entry_year_max
            if leg.entry_year_max_param == "new_year":
                hi = self.new_year
            resolved.append((leg.name, lo, hi))
        return tuple(resolved)

    @property
    def decrements_method(self) -> str:
        return self.decrements.method

    @property
    def max_entry_year(self) -> int:
        return self.ranges.max_entry_year

    @property
    def entry_year_range(self) -> range:
        return self.ranges.entry_year_range

    @property
    def age_range(self) -> range:
        return self.ranges.age_range

    @property
    def yos_range(self) -> range:
        return self.ranges.yos_range

    @property
    def max_year(self) -> int:
        return self.ranges.max_year

    @property
    def class_data(self) -> Dict[str, ClassData]:
        """Per-class merged view of valuation_inputs + calibration.

        Returns typed ``ClassData`` objects, one per class. Same
        access pattern as the prior ``SimpleNamespace`` shape:
        ``config.class_data[cn].nc_cal``, etc.
        """
        result = {}
        for class_name, valuation in self.valuation_inputs.items():
            cal = self.calibration.get(class_name)
            result[class_name] = ClassData(
                ben_payment=valuation.ben_payment,
                retiree_pop=valuation.retiree_pop,
                total_active_member=valuation.total_active_member,
                er_dc_cont_rate=valuation.er_dc_cont_rate,
                val_norm_cost=valuation.val_norm_cost,
                nc_cal=cal.nc_cal if cal is not None else 1.0,
                pvfb_term_current=cal.pvfb_term_current if cal is not None else 0.0,
            )
        return result

    @property
    def plan_design_defs(self) -> dict:
        """Backward-compat: raw dict of group → ratios mappings.

        Some legacy code (and the calibration runner) still iterates
        the raw shape. Builds a dict from the typed ``plan_design``
        each call.
        """
        return {
            name: ratios.model_dump(exclude_none=True)
            for name, ratios in self.plan_design.groups.items()
        }

    def get_design_ratios(self, class_name: str) -> Dict[str, Tuple[float, float, float]]:
        group_name = self.design_ratio_group_map.get(class_name, self.class_group(class_name))
        ratios = (
            self.plan_design.group(group_name)
            or self.plan_design.group("default")
            or PlanDesignRatios()
        )
        result = {}
        for bt in self.benefit_types:
            if bt == "db":
                result["db"] = ratios.db_triple()
            elif bt == "cb":
                result["cb"] = ratios.cb_triple()
            elif bt == "dc":
                db_before, db_after, db_new = result.get("db", (1.0, 1.0, 1.0))
                cb_before, cb_after, cb_new = result.get("cb", (0.0, 0.0, 0.0))
                result["dc"] = (
                    1.0 - db_before - cb_before,
                    1.0 - db_after - cb_after,
                    1.0 - db_new - cb_new,
                )
        return result

    def class_group(self, class_name: str) -> str:
        return self.class_to_group.get(class_name, "default")

    def resolve_ben_mult(
        self, class_name: str, tier_name: str
    ) -> Optional[MultiplierRules]:
        """Look up the typed :class:`MultiplierRules` for a (class, tier).

        Encapsulates the ``all_tiers`` / ``<tier>_same_as`` / direct
        resolution so consumers don't have to thread the lookup logic
        through dict access.
        """
        return self.benefit_mult_defs.resolve(class_name, tier_name)

    def get_class_inputs(self, class_name: str) -> dict:
        valuation = self.valuation_inputs.get(class_name)
        if valuation is None:
            return {"nc_cal": 1.0, "pvfb_term_current": 0.0}
        base = valuation.model_dump(exclude_none=True)
        cal = self.calibration.get(class_name)
        base["nc_cal"] = cal.nc_cal if cal is not None else 1.0
        base["pvfb_term_current"] = cal.pvfb_term_current if cal is not None else 0.0
        return base

    def validate(self) -> list:
        from pension_model.config_validation import validate_config
        return validate_config(self)

    def validate_data_files(self) -> list:
        from pension_model.config_validation import validate_data_files
        return validate_data_files(self)

    # ------------------------------------------------------------------
    # Underscore-name aliases for legacy resolver code that still reads
    # ``config._class_to_group`` etc. Defined as @property so they
    # don't conflict with pydantic's field-name expectations.
    # ------------------------------------------------------------------

    @property
    def _class_to_group(self) -> Dict[str, str]:
        return self.class_to_group

    @property
    def _tier_name_to_id(self) -> Dict[str, int]:
        return self.tier_name_to_id

    @property
    def _tier_id_to_name(self) -> Tuple[str, ...]:
        return self.tier_id_to_name

    @property
    def _tier_id_to_cola_key(self) -> Tuple[str, ...]:
        return self.tier_id_to_cola_key

    @property
    def _tier_id_to_fas_years(self) -> Tuple[int, ...]:
        return self.tier_id_to_fas_years

    @property
    def _tier_id_to_dr_key(self) -> Tuple[str, ...]:
        return self.tier_id_to_dr_key

    @property
    def _tier_id_to_retire_rate_set(self) -> Tuple[str, ...]:
        return self.tier_id_to_retire_rate_set
