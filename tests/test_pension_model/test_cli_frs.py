"""FRS-specific CLI target-selection tests."""

from pension_model.cli import _get_test_targets


def test_get_test_targets_frs_uses_only_frs_plan_files():
    targets = _get_test_targets("frs")
    assert "tests/test_pension_model/test_cli_frs.py" in targets
    assert "tests/test_pension_model/test_plan_config_frs.py" in targets
    assert "tests/test_pension_model/test_vectorized_resolvers_frs.py" in targets
    assert "tests/test_pension_model/test_data_integrity.py" in targets
    assert "tests/test_pension_model/test_truth_table_frs.py" in targets
    assert "tests/test_pension_model/test_cli_txtrs.py" not in targets
    assert "tests/test_pension_model/test_plan_config_txtrs.py" not in targets
    assert "tests/test_pension_model/test_vectorized_resolvers_txtrs.py" not in targets
    assert "tests/test_pension_model/test_truth_table_txtrs.py" not in targets
