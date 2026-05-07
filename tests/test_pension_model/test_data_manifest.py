"""Tests for ``data_manifest.json`` validation.

The manifest is the per-plan source of truth for required and optional
data files. ``validate_data_manifest`` reads it, expands per-class
templates, and returns missing required files.
"""

from __future__ import annotations

import json

import pytest

from pension_model.config_loading import load_plan_config_by_name
from pension_model.config_validation import (
    _expand_manifest_entry_paths,
    _resolve_manifest_path,
    validate_data_manifest,
)

pytestmark = [pytest.mark.unit]


@pytest.mark.parametrize("plan_name", ["frs", "txtrs", "txtrs-av"])
def test_plan_manifest_matches_disk(plan_name):
    """Each shipped plan's manifest agrees with files actually on disk."""
    config = load_plan_config_by_name(plan_name)
    missing = validate_data_manifest(config)
    assert missing == [], (
        f"Plan {plan_name!r} declares files in data_manifest.json that "
        f"do not exist on disk: {missing}"
    )


def test_no_manifest_returns_empty(tmp_path, monkeypatch):
    """Plans without a manifest validate trivially (additive behavior)."""
    config = load_plan_config_by_name("frs")
    fake_data_dir = tmp_path / "data"
    fake_data_dir.mkdir()
    monkeypatch.setattr(type(config), "resolve_data_dir", lambda self: fake_data_dir)
    # Sanity: no data_manifest.json adjacent to fake_data_dir
    assert not _resolve_manifest_path(config).exists()

    assert validate_data_manifest(config) == []


def test_missing_required_file_reported(tmp_path):
    """A required file declared in the manifest must exist."""
    plan_root = tmp_path / "plan_x"
    data_dir = plan_root / "data"
    (data_dir / "demographics").mkdir(parents=True)
    (plan_root / "data_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "files": [
                    {
                        "path": "demographics/retiree_distribution.csv",
                        "scope": "plan",
                        "required": True,
                        "purpose": "test",
                    },
                ],
            }
        )
    )

    class FakeConfig:
        classes = ("all",)
        plan_name = "plan_x"

        def resolve_data_dir(self):
            return data_dir

    missing = validate_data_manifest(FakeConfig())
    assert len(missing) == 1
    assert "retiree_distribution.csv" in missing[0]


def test_fallback_path_satisfies_requirement(tmp_path):
    """When the primary path is absent but the fallback exists, the
    requirement is satisfied."""
    plan_root = tmp_path / "plan_x"
    data_dir = plan_root / "data"
    (data_dir / "demographics").mkdir(parents=True)
    # Only the fallback file exists, not the per-class primary
    (data_dir / "demographics" / "salary_growth.csv").write_text("yos,growth\n")
    (plan_root / "data_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "files": [
                    {
                        "path": "demographics/{class_name}_salary_growth.csv",
                        "scope": "per_class",
                        "required": True,
                        "fallback": "demographics/salary_growth.csv",
                        "purpose": "test",
                    },
                ],
            }
        )
    )

    class FakeConfig:
        classes = ("all",)
        plan_name = "plan_x"

        def resolve_data_dir(self):
            return data_dir

    assert validate_data_manifest(FakeConfig()) == []


def test_optional_files_are_not_required(tmp_path):
    """Optional files do not surface as missing."""
    plan_root = tmp_path / "plan_x"
    data_dir = plan_root / "data"
    data_dir.mkdir(parents=True)
    (plan_root / "data_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "files": [
                    {
                        "path": "demographics/entrant_profile.csv",
                        "scope": "plan",
                        "required": False,
                        "purpose": "test",
                    },
                ],
            }
        )
    )

    class FakeConfig:
        classes = ("all",)
        plan_name = "plan_x"

        def resolve_data_dir(self):
            return data_dir

    assert validate_data_manifest(FakeConfig()) == []


def test_per_class_expansion():
    """Per-class entries expand once per class, with the class_name
    placeholder substituted."""
    entry = {
        "path": "demographics/{class_name}_salary.csv",
        "scope": "per_class",
    }
    paths = _expand_manifest_entry_paths(entry, ["regular", "special", "admin"])
    assert paths == [
        "demographics/regular_salary.csv",
        "demographics/special_salary.csv",
        "demographics/admin_salary.csv",
    ]


def test_plan_scope_returns_single_path():
    entry = {
        "path": "mortality/base_rates.csv",
        "scope": "plan",
    }
    assert _expand_manifest_entry_paths(entry, ["regular", "special"]) == [
        "mortality/base_rates.csv",
    ]
