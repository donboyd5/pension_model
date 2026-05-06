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
    Decrements,
    Economic,
    Modeling,
    Ranges,
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
