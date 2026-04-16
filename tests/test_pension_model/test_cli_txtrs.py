"""TXTRS-specific CLI target-selection tests."""

from pension_model.cli import _get_test_targets


def test_get_test_targets_txtrs_uses_only_txtrs_plan_files():
    targets = _get_test_targets("txtrs")
    assert "tests/test_pension_model/test_cli_txtrs.py" in targets
    assert "tests/test_pension_model/test_plan_config_txtrs.py" in targets
    assert "tests/test_pension_model/test_vectorized_resolvers_txtrs.py" in targets
    assert "tests/test_pension_model/test_truth_table_txtrs.py" in targets
    assert "tests/test_pension_model/test_cli_frs.py" not in targets
    assert "tests/test_pension_model/test_plan_config_frs.py" not in targets
    assert "tests/test_pension_model/test_vectorized_resolvers_frs.py" not in targets
    assert "tests/test_pension_model/test_truth_table_frs.py" not in targets
    assert "tests/test_pension_model/test_data_integrity.py" not in targets
