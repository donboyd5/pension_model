"""CLI ergonomics tests: --full-suite scope and validate-scenarios."""

from __future__ import annotations

import subprocess

import pytest

from pension_model.cli import _discover_scenarios, _get_test_targets

pytestmark = [pytest.mark.unit]


def test_full_suite_scope_uses_repository_targets():
    assert _get_test_targets(None) == ["tests/test_pension_model/"]


def test_plan_scoped_targets_include_core_and_manifest():
    targets = _get_test_targets("frs")
    assert any("test_cli_shared.py" in t for t in targets)
    assert any("frs" in t for t in targets)
    assert "tests/test_pension_model/" not in targets


def test_validate_scenarios_subcommand_passes_for_existing_scenarios():
    """All shipped (plan, scenario) pairs must validate cleanly."""
    result = subprocess.run(
        ["pension-model", "validate-scenarios"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"validate-scenarios failed:\n{result.stdout}\n{result.stderr}"
    assert "All" in result.stdout and "validated" in result.stdout


def test_validate_scenarios_filters_by_plan():
    result = subprocess.run(
        ["pension-model", "validate-scenarios", "--plan", "txtrs"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "txtrs" in result.stdout
    # FRS pairs should not appear when filtering to txtrs
    assert "  ok    frs " not in result.stdout


def test_discover_scenarios_finds_shipped_scenarios():
    scenarios = _discover_scenarios()
    assert "asset_shock" in scenarios
    assert "high_discount" in scenarios
    assert "low_return" in scenarios
    assert "no_cola" in scenarios
