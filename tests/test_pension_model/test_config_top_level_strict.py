"""Top-level PlanConfig must reject unknown keys.

Phase A robustness gate. Before this change, ``PlanConfig`` used
``extra="ignore"`` at the top level, so a typo like ``valuation_inputs_notes``
loaded silently. The pydantic schema now uses ``extra="forbid"`` and the
loader runs an explicit unknown-key check. Documentation belongs in the
typed ``notes`` block.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pension_model.config_loading import (
    check_unknown_top_level_keys,
    load_plan_config,
    load_plan_config_by_name,
)


pytestmark = [pytest.mark.unit]


def _load_raw(plan_name: str) -> dict:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "plans" / plan_name / "config" / "plan_config.json"
    return json.loads(path.read_text())


def test_top_level_typo_is_rejected():
    """A typo'd top-level section name must fail load."""
    raw = _load_raw("frs")
    raw["economics"] = raw.pop("economic")

    with pytest.raises(ValueError) as excinfo:
        check_unknown_top_level_keys(raw)

    assert "economics" in str(excinfo.value)


def test_unknown_top_level_notes_key_is_rejected():
    """Old-style ``*_notes`` top-level keys are rejected; documentation
    moves into the typed ``notes`` block instead."""
    raw = _load_raw("txtrs")
    raw["valuation_inputs_notes"] = "stale documentation key"

    with pytest.raises(ValueError) as excinfo:
        check_unknown_top_level_keys(raw)

    assert "valuation_inputs_notes" in str(excinfo.value)


def test_loader_rejects_unknown_top_level_key(tmp_path):
    """The full loader path also rejects unknown top-level keys."""
    raw = _load_raw("txtrs")
    raw["bogus_key"] = 42
    cfg_path = tmp_path / "plan_config.json"
    cfg_path.write_text(json.dumps(raw))

    with pytest.raises(ValueError) as excinfo:
        load_plan_config(cfg_path)

    assert "bogus_key" in str(excinfo.value)


def test_typed_notes_block_loads_via_full_loader(tmp_path):
    """The ``notes`` block accepts arbitrary key/value documentation."""
    raw = _load_raw("txtrs")
    raw["notes"] = {
        "design_ratio_group_map": "free-text explanation",
        "valuation_inputs": {"source": "2023 AV", "page": 42},
    }
    cfg_path = tmp_path / "plan_config.json"
    cfg_path.write_text(json.dumps(raw))

    config = load_plan_config(cfg_path)

    assert config.notes["design_ratio_group_map"] == "free-text explanation"
    assert config.notes["valuation_inputs"]["page"] == 42


def test_frs_loads_with_migrated_notes():
    """FRS config carries documentation in the ``notes`` block."""
    config = load_plan_config_by_name("frs")

    assert "design_ratio_group_map" in config.notes
    assert "valuation_inputs" in config.notes
