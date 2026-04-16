"""TXTRS-specific PlanConfig tests."""

import pytest

pytestmark = [pytest.mark.unit]

from pension_model.plan_config import load_txtrs_config


def test_txtrs_loads():
    config = load_txtrs_config()
    assert config.plan_name == "txtrs"
    assert len(config.classes) == 1
    assert config.classes[0] == "all"
    assert config.dr_current == 0.07
    assert config.db_ee_cont_rate == 0.0825
    assert config.cash_balance is not None
    assert config.cash_balance["ee_pay_credit"] == 0.06
