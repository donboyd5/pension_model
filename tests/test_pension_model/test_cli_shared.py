"""Shared CLI-level unit tests for plan-scoped helpers."""

from pension_model.cli import _get_test_targets


def test_get_test_targets_full_suite_uses_repository_scope():
    assert _get_test_targets(None) == ["tests/test_pension_model/"]
