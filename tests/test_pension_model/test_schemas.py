"""Schema validation tests for the pydantic models in
``pension_model.schemas``.

For each model: missing required field raises, extra field raises
under strict mode, defaults apply correctly, computed properties work.
"""

import pytest

pytestmark = [pytest.mark.unit]

from pydantic import ValidationError

from pension_model.schemas import (
    AgeGroup,
    AvaSmoothing,
    Benefit,
    BenefitMultipliers,
    Calibration,
    CashBalance,
    ClassCalibration,
    ClassMultipliers,
    Cola,
    Condition,
    CorridorAvaSmoothing,
    DcSpec,
    Decrements,
    Economic,
    FlatBeforeYear,
    Funding,
    GainLossAvaSmoothing,
    GradedRule,
    LegDef,
    Modeling,
    MultiplierRules,
    PlanDesign,
    PlanDesignRatios,
    RampSpec,
    Ranges,
    RateComponentSpec,
    RateScheduleEntry,
    StatutoryRates,
    ValuationInputs,
)


# ---------------------------------------------------------------------------
# Economic
# ---------------------------------------------------------------------------


class TestEconomic:
    def _valid(self, **overrides):
        base = {
            "dr_current": 0.067,
            "dr_new": 0.067,
            "payroll_growth": 0.0325,
            "baseline_dr_current": 0.067,
            "baseline_model_return": 0.067,
        }
        base.update(overrides)
        return base

    def test_loads_with_required_fields(self):
        econ = Economic.model_validate(self._valid())
        assert econ.dr_current == 0.067
        assert econ.payroll_growth == 0.0325

    def test_dr_old_defaults_to_dr_current(self):
        econ = Economic.model_validate(self._valid())
        assert econ.dr_old == econ.dr_current

    def test_dr_old_explicit_value_preserved(self):
        econ = Economic.model_validate(self._valid(dr_old=0.068))
        assert econ.dr_old == 0.068

    def test_model_return_defaults_to_dr_current(self):
        econ = Economic.model_validate(self._valid())
        assert econ.model_return == econ.dr_current

    def test_pop_growth_defaults_to_zero(self):
        econ = Economic.model_validate(self._valid())
        assert econ.pop_growth == 0.0

    def test_missing_required_field_raises(self):
        bad = self._valid()
        del bad["dr_current"]
        with pytest.raises(ValidationError, match="dr_current"):
            Economic.model_validate(bad)

    def test_extra_field_raises(self):
        bad = self._valid(dr_currnt=0.067)  # typo
        with pytest.raises(ValidationError, match="dr_currnt"):
            Economic.model_validate(bad)


# ---------------------------------------------------------------------------
# Ranges
# ---------------------------------------------------------------------------


class TestRanges:
    def _valid(self, **overrides):
        base = {
            "min_age": 18,
            "max_age": 120,
            "start_year": 2022,
            "new_year": 2024,
            "min_entry_year": 1970,
            "model_period": 30,
            "max_yos": 70,
        }
        base.update(overrides)
        return base

    def test_loads_with_required_fields(self):
        r = Ranges.model_validate(self._valid())
        assert r.min_age == 18
        assert r.start_year == 2022

    def test_new_year_defaults_to_start_year(self):
        r = Ranges.model_validate(self._valid(new_year=None))
        assert r.new_year == 2022

    def test_max_entry_year_computed(self):
        r = Ranges.model_validate(self._valid())
        assert r.max_entry_year == 2052  # start_year + model_period

    def test_entry_year_range_computed(self):
        r = Ranges.model_validate(self._valid())
        assert r.entry_year_range == range(1970, 2053)

    def test_age_range_computed(self):
        r = Ranges.model_validate(self._valid())
        assert r.age_range == range(18, 121)

    def test_extra_field_raises(self):
        with pytest.raises(ValidationError, match="strart_year"):
            Ranges.model_validate(self._valid(strart_year=2022))


# ---------------------------------------------------------------------------
# Decrements
# ---------------------------------------------------------------------------


class TestDecrements:
    def test_yos_only_loads(self):
        d = Decrements.model_validate({"method": "yos_only"})
        assert d.method == "yos_only"

    def test_years_from_nr_loads(self):
        d = Decrements.model_validate({"method": "years_from_nr"})
        assert d.method == "years_from_nr"

    def test_unknown_method_raises(self):
        with pytest.raises(ValidationError, match="made_up"):
            Decrements.model_validate({"method": "made_up"})

    def test_missing_method_raises(self):
        with pytest.raises(ValidationError, match="method"):
            Decrements.model_validate({})


# ---------------------------------------------------------------------------
# Modeling and AgeGroup
# ---------------------------------------------------------------------------


class TestModeling:
    def test_empty_loads_with_defaults(self):
        m = Modeling.model_validate({})
        assert m.entrant_salary_at_start_year is False
        assert m.use_earliest_retire is False
        assert m.male_mp_forward_shift == 0
        assert m.age_groups is None

    def test_age_groups_typed(self):
        m = Modeling.model_validate({
            "age_groups": [
                {"label": "young", "max_age": 30},
                {"label": "mid", "min_age": 31, "max_age": 50},
                {"label": "old", "min_age": 51},
            ],
        })
        assert m.age_groups is not None
        assert len(m.age_groups) == 3
        assert isinstance(m.age_groups[0], AgeGroup)
        assert m.age_groups[0].label == "young"
        assert m.age_groups[0].max_age == 30
        assert m.age_groups[0].min_age is None  # open-ended low
        assert m.age_groups[2].max_age is None  # open-ended high

    def test_extra_field_in_age_group_raises(self):
        with pytest.raises(ValidationError, match="lable"):
            Modeling.model_validate({
                "age_groups": [{"lable": "young"}],  # typo
            })

    def test_extra_top_level_field_raises(self):
        with pytest.raises(ValidationError, match="bogus"):
            Modeling.model_validate({"bogus": True})


# ---------------------------------------------------------------------------
# AvaSmoothing (discriminated union)
# ---------------------------------------------------------------------------


class TestAvaSmoothing:
    def test_corridor_method_dispatches_to_corridor_model(self):
        sm = CorridorAvaSmoothing.model_validate({"method": "corridor"})
        assert sm.corridor_low == 0.8
        assert sm.corridor_high == 1.2
        assert sm.recognition_fraction == 0.2

    def test_corridor_with_explicit_values(self):
        sm = CorridorAvaSmoothing.model_validate({
            "method": "corridor",
            "corridor_low": 0.7,
            "corridor_high": 1.3,
            "recognition_fraction": 0.25,
        })
        assert sm.corridor_low == 0.7
        assert sm.recognition_fraction == 0.25

    def test_gain_loss_method(self):
        sm = GainLossAvaSmoothing.model_validate({
            "method": "gain_loss",
            "recognition_period": 4,
        })
        assert sm.recognition_period == 4

    def test_gain_loss_missing_recognition_period_raises(self):
        with pytest.raises(ValidationError, match="recognition_period"):
            GainLossAvaSmoothing.model_validate({"method": "gain_loss"})


# ---------------------------------------------------------------------------
# RateComponentSpec (mutual-exclusion validator)
# ---------------------------------------------------------------------------


class TestRateComponentSpec:
    def test_schedule_form_loads(self):
        c = RateComponentSpec.model_validate({
            "name": "base",
            "payroll_share": 1.0,
            "schedule": [{"from_year": 0, "rate": 0.08}],
        })
        assert c.schedule is not None
        assert c.ramp is None

    def test_ramp_form_loads(self):
        c = RateComponentSpec.model_validate({
            "name": "surcharge",
            "payroll_share": 0.5,
            "initial_rate": 0.0,
            "ramp": {"rate_per_year": 0.001, "end_year": 2030},
        })
        assert c.ramp is not None
        assert c.schedule is None

    def test_neither_schedule_nor_ramp_raises(self):
        with pytest.raises(ValidationError, match="must specify either"):
            RateComponentSpec.model_validate({
                "name": "no_rate",
            })

    def test_both_schedule_and_ramp_raises(self):
        with pytest.raises(ValidationError, match="mutually exclusive"):
            RateComponentSpec.model_validate({
                "name": "both",
                "schedule": [{"from_year": 0, "rate": 0.08}],
                "ramp": {"rate_per_year": 0.001, "end_year": 2030},
            })


# ---------------------------------------------------------------------------
# Funding (top-level + cross-field validator)
# ---------------------------------------------------------------------------


class TestFunding:
    def _valid_actuarial(self, **overrides):
        base = {
            "contribution_strategy": "actuarial",
            "policy": "statutory",
            "amo_method": "level_pct",
            "amo_period_new": 20,
            "amo_pay_growth": 0.0325,
            "ava_smoothing": {"method": "corridor"},
        }
        base.update(overrides)
        return base

    def _valid_statutory(self, **overrides):
        base = self._valid_actuarial()
        base.update({
            "contribution_strategy": "statutory",
            "ava_smoothing": {"method": "gain_loss", "recognition_period": 4},
            "statutory_rates": {
                "ee_rate_schedule": [{"from_year": 0, "rate": 0.08}],
                "er_rate_components": [
                    {
                        "name": "base",
                        "schedule": [{"from_year": 0, "rate": 0.08}],
                    },
                ],
            },
        })
        base.update(overrides)
        return base

    def test_actuarial_loads(self):
        f = Funding.model_validate(self._valid_actuarial())
        assert f.contribution_strategy == "actuarial"
        assert isinstance(f.ava_smoothing, CorridorAvaSmoothing)

    def test_statutory_loads(self):
        f = Funding.model_validate(self._valid_statutory())
        assert f.contribution_strategy == "statutory"
        assert isinstance(f.ava_smoothing, GainLossAvaSmoothing)
        assert f.statutory_rates is not None

    def test_statutory_without_rates_block_raises(self):
        bad = self._valid_actuarial()
        bad["contribution_strategy"] = "statutory"
        with pytest.raises(ValidationError, match="statutory_rates is missing"):
            Funding.model_validate(bad)

    def test_unknown_contribution_strategy_raises(self):
        bad = self._valid_actuarial()
        bad["contribution_strategy"] = "made_up"
        with pytest.raises(ValidationError, match="made_up"):
            Funding.model_validate(bad)

    def test_default_legs(self):
        f = Funding.model_validate(self._valid_actuarial())
        assert len(f.legs) == 2
        assert f.legs[0].name == "legacy"
        assert f.legs[0].entry_year_max_param == "new_year"
        assert f.legs[1].name == "new"
        assert f.legs[1].entry_year_min_param == "new_year"

    def test_explicit_legs_override_default(self):
        f = Funding.model_validate(self._valid_actuarial(legs=[
            {"name": "before_2011", "entry_year_max": 2011},
            {"name": "from_2011", "entry_year_min": 2011},
        ]))
        assert [leg.name for leg in f.legs] == ["before_2011", "from_2011"]

    def test_extra_field_raises(self):
        with pytest.raises(ValidationError, match="bogus_field"):
            Funding.model_validate(self._valid_actuarial(bogus_field=1))


# ---------------------------------------------------------------------------
# Cola (extra=allow for per-tier dynamic keys)
# ---------------------------------------------------------------------------


class TestCola:
    def test_empty_loads_with_defaults(self):
        c = Cola.model_validate({})
        assert c.current_retire == 0.0
        assert c.proration_cutoff_year is None

    def test_per_tier_keys_admitted_as_extras(self):
        c = Cola.model_validate({
            "current_retire": 0.03,
            "tier_1_active": 0.03,
            "tier_2_active": 0.0,
            "tier_1_active_constant": False,
        })
        assert c.current_retire == 0.03
        # Per-tier keys readable via getattr (not part of typed fields).
        assert getattr(c, "tier_1_active") == 0.03
        assert getattr(c, "tier_2_active") == 0.0
        assert getattr(c, "tier_1_active_constant") is False
        assert getattr(c, "missing_key", "fallback") == "fallback"


# ---------------------------------------------------------------------------
# CashBalance
# ---------------------------------------------------------------------------


class TestCashBalance:
    def test_required_fields(self):
        cb = CashBalance.model_validate({
            "ee_pay_credit": 0.06,
            "er_pay_credit": 0.09,
            "vesting_yos": 5,
            "icr_smooth_period": 5,
            "icr_floor": 0.04,
            "icr_cap": 0.07,
            "icr_upside_share": 0.5,
            "annuity_conversion_rate": 0.04,
        })
        assert cb.ee_pay_credit == 0.06
        assert cb.return_volatility == 0.12  # default

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError, match="vesting_yos"):
            CashBalance.model_validate({
                "ee_pay_credit": 0.06,
                "er_pay_credit": 0.09,
                "icr_smooth_period": 5,
                "icr_floor": 0.04,
                "icr_cap": 0.07,
                "icr_upside_share": 0.5,
                "annuity_conversion_rate": 0.04,
            })

    def test_extra_field_raises(self):
        with pytest.raises(ValidationError, match="extra_thing"):
            CashBalance.model_validate({
                "ee_pay_credit": 0.06,
                "er_pay_credit": 0.09,
                "vesting_yos": 5,
                "icr_smooth_period": 5,
                "icr_floor": 0.04,
                "icr_cap": 0.07,
                "icr_upside_share": 0.5,
                "annuity_conversion_rate": 0.04,
                "extra_thing": True,
            })


# ---------------------------------------------------------------------------
# Benefit (top-level + composition)
# ---------------------------------------------------------------------------


class TestBenefit:
    def _valid(self, **overrides):
        base = {
            "db_ee_cont_rate": 0.03,
            "fas_years_default": 5,
            "benefit_types": ["db"],
        }
        base.update(overrides)
        return base

    def test_minimal_loads(self):
        b = Benefit.model_validate(self._valid())
        assert b.db_ee_cont_rate == 0.03
        assert b.cola.current_retire == 0.0  # default Cola
        assert b.cash_balance is None
        assert b.dc is None

    def test_with_cola_and_cb(self):
        b = Benefit.model_validate(self._valid(
            cola={"current_retire": 0.03, "tier_1_active": 0.03},
            cash_balance={
                "ee_pay_credit": 0.06,
                "er_pay_credit": 0.09,
                "vesting_yos": 5,
                "icr_smooth_period": 5,
                "icr_floor": 0.04,
                "icr_cap": 0.07,
                "icr_upside_share": 0.5,
                "annuity_conversion_rate": 0.04,
            },
        ))
        assert b.cola.current_retire == 0.03
        assert getattr(b.cola, "tier_1_active") == 0.03
        assert b.cash_balance is not None
        assert b.cash_balance.ee_pay_credit == 0.06

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError, match="db_ee_cont_rate"):
            Benefit.model_validate({"fas_years_default": 5})

    def test_extra_field_raises(self):
        with pytest.raises(ValidationError, match="bogus"):
            Benefit.model_validate(self._valid(bogus=1))


# ---------------------------------------------------------------------------
# ValuationInputs
# ---------------------------------------------------------------------------


class TestValuationInputs:
    def _valid(self, **overrides):
        base = {
            "ben_payment": 1.0e9,
            "retiree_pop": 1000,
            "total_active_member": 5000,
            "val_norm_cost": 0.10,
        }
        base.update(overrides)
        return base

    def test_minimal_loads(self):
        v = ValuationInputs.model_validate(self._valid())
        assert v.ben_payment == 1.0e9
        assert v.er_dc_cont_rate == 0.0  # default
        assert v.headcount_group is None

    def test_with_headcount_group(self):
        v = ValuationInputs.model_validate(
            self._valid(headcount_group=["a", "b", "c"])
        )
        assert v.headcount_group == ["a", "b", "c"]

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError, match="ben_payment"):
            ValuationInputs.model_validate({
                "retiree_pop": 1000,
                "total_active_member": 5000,
                "val_norm_cost": 0.10,
            })

    def test_extra_field_raises(self):
        with pytest.raises(ValidationError, match="extra_thing"):
            ValuationInputs.model_validate(self._valid(extra_thing=1))


# ---------------------------------------------------------------------------
# Calibration + ClassCalibration
# ---------------------------------------------------------------------------


class TestCalibration:
    def test_classcalibration_defaults(self):
        c = ClassCalibration.model_validate({})
        assert c.nc_cal == 1.0
        assert c.pvfb_term_current == 0.0

    def test_calibration_loads_classes_dict(self):
        c = Calibration.model_validate({
            "cal_factor": 0.9,
            "classes": {
                "regular": {"nc_cal": 0.985, "pvfb_term_current": 6e9},
                "special": {"nc_cal": 1.0, "pvfb_term_current": 0.0},
            },
        })
        assert c.cal_factor == 0.9
        assert isinstance(c.classes["regular"], ClassCalibration)
        assert c.classes["regular"].nc_cal == 0.985

    def test_documentation_fields_optional(self):
        c = Calibration.model_validate({
            "description": "FRS 2022 calibration",
            "cal_factor": 0.9,
        })
        assert c.description == "FRS 2022 calibration"

    def test_extra_admitted(self):
        # Calibration uses extra="allow" so future fields don't break.
        c = Calibration.model_validate({"future_field": "ok"})
        assert "future_field" in (c.model_extra or {})


# ---------------------------------------------------------------------------
# PlanDesign + PlanDesignRatios
# ---------------------------------------------------------------------------


class TestPlanDesign:
    def test_db_triple_with_full_fields(self):
        r = PlanDesignRatios.model_validate({
            "before_cutoff": 0.95,
            "after_cutoff": 0.85,
            "new": 0.75,
        })
        assert r.db_triple() == (0.95, 0.85, 0.75)

    def test_db_triple_after_defaults_to_before(self):
        r = PlanDesignRatios.model_validate({"before_cutoff": 0.75})
        assert r.db_triple() == (0.75, 0.75, 1.0)

    def test_db_triple_uses_new_db_when_new_absent(self):
        r = PlanDesignRatios.model_validate({"before_cutoff": 1.0, "new_db": 0.5})
        assert r.db_triple() == (1.0, 1.0, 0.5)

    def test_cb_triple_defaults_to_zero(self):
        r = PlanDesignRatios.model_validate({})
        assert r.cb_triple() == (0.0, 0.0, 0.0)

    def test_groups_promoted_to_typed_at_parse(self):
        pd = PlanDesign.model_validate({
            "cutoff_year": 2018,
            "regular_group": {"before_cutoff": 0.75, "new": 0.25},
            "special_group": {"before_cutoff": 0.95, "after_cutoff": 0.85, "new": 0.75},
        })
        assert pd.cutoff_year == 2018
        assert isinstance(pd.group("regular_group"), PlanDesignRatios)
        assert pd.group("regular_group").before_cutoff == 0.75
        assert set(pd.groups) == {"regular_group", "special_group"}
        assert pd.group("missing") is None


# ---------------------------------------------------------------------------
# Condition (shared predicate)
# ---------------------------------------------------------------------------


class TestCondition:
    def test_empty_condition_loads(self):
        c = Condition.model_validate({})
        assert c.min_age is None and c.min_yos is None and c.rule_of is None

    def test_typical_fields(self):
        c = Condition.model_validate({"min_age": 65, "min_yos": 6})
        assert c.min_age == 65
        assert c.min_yos == 6

    def test_extra_field_raises(self):
        with pytest.raises(ValidationError, match="bogus"):
            Condition.model_validate({"min_age": 65, "bogus": 1})


# ---------------------------------------------------------------------------
# MultiplierRules (primary-rule mutual exclusion)
# ---------------------------------------------------------------------------


class TestMultiplierRules:
    def test_flat_only_loads(self):
        r = MultiplierRules.model_validate({"flat": 0.023})
        assert r.flat == 0.023

    def test_graded_only_loads(self):
        r = MultiplierRules.model_validate({
            "graded": [
                {"or": [{"min_age": 65}], "mult": 0.02},
            ],
        })
        assert r.graded is not None
        assert len(r.graded) == 1
        assert r.graded[0].mult == 0.02
        assert r.graded[0].or_[0].min_age == 65

    def test_flat_with_flat_before_year(self):
        r = MultiplierRules.model_validate({
            "flat": 0.03,
            "flat_before_year": {"year": 1974, "mult": 0.02},
        })
        assert r.flat_before_year is not None
        assert r.flat_before_year.year == 1974

    def test_neither_flat_nor_graded_raises(self):
        with pytest.raises(ValidationError, match="must declare either"):
            MultiplierRules.model_validate({"early_fallback": 0.01})

    def test_both_flat_and_graded_raises(self):
        with pytest.raises(ValidationError, match="mutually exclusive"):
            MultiplierRules.model_validate({
                "flat": 0.02,
                "graded": [{"or": [{"min_age": 65}], "mult": 0.02}],
            })

    def test_flat_before_year_without_flat_raises(self):
        with pytest.raises(ValidationError, match="requires 'flat'"):
            MultiplierRules.model_validate({
                "graded": [{"or": [{"min_age": 65}], "mult": 0.02}],
                "flat_before_year": {"year": 1974, "mult": 0.02},
            })


# ---------------------------------------------------------------------------
# BenefitMultipliers (lookup + same_as resolution)
# ---------------------------------------------------------------------------


class TestBenefitMultipliers:
    def _frs_like(self):
        return {
            "regular": {
                "tier_1": {"flat": 0.0168},
                "tier_2": {"flat": 0.016},
                "tier_3_same_as": "tier_2",
            },
            "judges": {
                "all_tiers": {"flat": 0.0333},
            },
        }

    def test_resolve_direct_tier(self):
        bm = BenefitMultipliers.model_validate(self._frs_like())
        rules = bm.resolve("regular", "tier_1")
        assert isinstance(rules, MultiplierRules)
        assert rules.flat == 0.0168

    def test_resolve_all_tiers(self):
        bm = BenefitMultipliers.model_validate(self._frs_like())
        rules = bm.resolve("judges", "tier_1")
        assert rules is not None and rules.flat == 0.0333
        # Any tier name resolves the same way under all_tiers.
        assert bm.resolve("judges", "tier_99").flat == 0.0333

    def test_resolve_same_as_alias(self):
        bm = BenefitMultipliers.model_validate(self._frs_like())
        rules = bm.resolve("regular", "tier_3")
        assert rules is not None and rules.flat == 0.016  # tier_2's value

    def test_resolve_unknown_class(self):
        bm = BenefitMultipliers.model_validate(self._frs_like())
        assert bm.resolve("nonexistent", "tier_1") is None

    def test_resolve_unknown_tier(self):
        bm = BenefitMultipliers.model_validate({
            "regular": {"tier_1": {"flat": 0.02}},
        })
        assert bm.resolve("regular", "tier_2") is None
