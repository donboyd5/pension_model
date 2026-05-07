"""Validation helpers for loaded plan configs."""

from __future__ import annotations

import json
from pathlib import Path


def validate_funding_legs(config) -> None:
    """Fatal check: funding legs are non-overlapping and cover the full
    entry-year range of the model.

    Currently also enforces exactly two legs — the simulation's
    funding-frame columns are hardcoded to two leg names (today
    ``legacy`` / ``new``). Generalization to N legs is tracked in
    Phase C9 (#137).

    Raises:
        ValueError: if leg count is not 2, if any two legs overlap, or
        if any entry year in ``[min_entry_year, max_entry_year)`` is
        not covered by exactly one leg.
    """
    legs = config.funding_legs
    if len(legs) != 2:
        raise ValueError(
            f"Plan {config.plan_name!r}: funding.legs must declare "
            f"exactly two legs (today's column-name shape requires it). "
            f"Got {len(legs)}: {[n for n, _, _ in legs]}. "
            f"N-leg generalization tracked in #137."
        )

    lo_bound = config.min_entry_year
    hi_bound = config.max_entry_year + 1  # max_entry_year is inclusive in usage

    for ey in range(lo_bound, hi_bound):
        matches = [
            name for name, lo, hi in legs
            if (lo is None or ey >= lo) and (hi is None or ey < hi)
        ]
        if len(matches) == 0:
            raise ValueError(
                f"Plan {config.plan_name!r}: entry_year {ey} is not "
                f"covered by any funding leg. Legs: "
                f"{[(n, lo, hi) for n, lo, hi in legs]}."
            )
        if len(matches) > 1:
            raise ValueError(
                f"Plan {config.plan_name!r}: entry_year {ey} is covered "
                f"by multiple funding legs {matches}. Legs must not "
                f"overlap. Legs: {[(n, lo, hi) for n, lo, hi in legs]}."
            )


def validate_config(config) -> list[str]:
    """Return non-fatal config warnings for a loaded plan."""
    warnings: list[str] = []

    # ben_payment is required by ValuationInputs; the schema would
    # have failed to load if it were missing. The check is kept here
    # as a no-op for forward compat.
    for class_name, calibration in config.calibration.items():
        nc_cal = calibration.nc_cal
        if nc_cal < 0.8 or nc_cal > 1.2:
            warnings.append(
                f"class '{class_name}' has nc_cal={nc_cal:.3f} (outside 0.8-1.2 range). "
                f"This may indicate data or assumption issues."
            )

    data_dir = config.resolve_data_dir()
    has_explicit_ep = (data_dir / "demographics" / "entrant_profile.csv").exists()
    if has_explicit_ep and not config.entrant_salary_at_start_year:
        warnings.append(
            "entrant_profile.csv exists but entrant_salary_at_start_year is not set. "
            "The profile salaries may not be scaled correctly."
        )

    for class_name in config.classes:
        if class_name not in config.valuation_inputs:
            warnings.append(
                f"class '{class_name}' is listed in 'classes' but has no entry in valuation_inputs."
            )

    # er_dc_cont_rate has a default of 0.0 in the schema. Only warn
    # if the plan declares dc but the rate is zero (likely
    # under-configured).
    if "dc" in config.benefit_types:
        for class_name in config.classes:
            valuation = config.valuation_inputs.get(class_name)
            if valuation is not None and valuation.er_dc_cont_rate == 0.0:
                warnings.append(
                    f"class '{class_name}' has er_dc_cont_rate=0.0 in valuation_inputs "
                    f"but benefit_types includes 'dc'."
                )

    for class_name, valuation in config.valuation_inputs.items():
        headcount_group = valuation.headcount_group
        if headcount_group and len(headcount_group) > 1:
            target = valuation.total_active_member
            for peer in headcount_group:
                peer_val = config.valuation_inputs.get(peer)
                peer_target = peer_val.total_active_member if peer_val is not None else None
                if peer_target != target:
                    warnings.append(
                        f"headcount_group mismatch: '{class_name}' has total_active_member={target} "
                        f"but peer '{peer}' has {peer_target}."
                    )
                    break

    return warnings


def validate_data_files(config) -> list[str]:
    """Return missing canonical data files for a plan."""
    missing: list[str] = []
    data_dir = config.resolve_data_dir()
    demographics_dir = data_dir / "demographics"

    for class_name in config.classes:
        for suffix in ("headcount", "salary"):
            prefixed = demographics_dir / f"{class_name}_{suffix}.csv"
            unprefixed = demographics_dir / f"{suffix}.csv"
            if not prefixed.exists() and not unprefixed.exists():
                missing.append(str(prefixed))

    has_any_sg = any(
        (demographics_dir / f"{class_name}_salary_growth.csv").exists()
        for class_name in config.classes
    )
    if not has_any_sg and not (demographics_dir / "salary_growth.csv").exists():
        missing.append(str(demographics_dir / "salary_growth.csv"))
    if not (demographics_dir / "retiree_distribution.csv").exists():
        missing.append(str(demographics_dir / "retiree_distribution.csv"))

    decrements_dir = data_dir / "decrements"
    for class_name in config.classes:
        for suffix in ("termination_rates", "retirement_rates"):
            prefixed = decrements_dir / f"{class_name}_{suffix}.csv"
            unprefixed = decrements_dir / f"{suffix}.csv"
            if not prefixed.exists() and not unprefixed.exists():
                missing.append(str(prefixed))

    mortality_dir = data_dir / "mortality"
    for filename in ("base_rates.csv", "improvement_scale.csv"):
        if not (mortality_dir / filename).exists():
            missing.append(str(mortality_dir / filename))

    funding_dir = data_dir / "funding"
    if not (funding_dir / "init_funding.csv").exists():
        missing.append(str(funding_dir / "init_funding.csv"))

    return missing


def _resolve_manifest_path(config) -> Path:
    """Return the expected location of this plan's data manifest.

    The manifest lives at ``plans/<plan>/data_manifest.json`` — sibling
    to the ``config/`` and ``data/`` directories.
    """
    return config.resolve_data_dir().parent / "data_manifest.json"


def _expand_manifest_entry_paths(entry: dict, classes: list[str]) -> list[str]:
    """Expand a manifest entry's ``path`` field for its declared scope."""
    scope = entry.get("scope", "plan")
    template = entry["path"]
    if scope == "per_class":
        return [template.format(**{"class_name": cn}) for cn in classes]
    return [template]


def validate_data_manifest(config) -> list[str]:
    """Return missing required files per the plan's ``data_manifest.json``.

    A manifest is the per-plan source of truth for what data files the
    plan needs. Each entry declares ``path`` (with optional
    ``{class_name}`` placeholder), ``scope`` (``"plan"`` or
    ``"per_class"``), ``required``, and an optional ``fallback`` path
    (an alternate location that, if present, satisfies the entry).

    Returns an empty list if the plan has no manifest, so this check is
    additive — not a replacement for :func:`validate_data_files`.
    """
    manifest_path = _resolve_manifest_path(config)
    if not manifest_path.exists():
        return []

    manifest = json.loads(manifest_path.read_text())
    data_dir = config.resolve_data_dir()
    classes = list(config.classes)

    missing: list[str] = []
    for entry in manifest.get("files", []):
        if not entry.get("required", False):
            continue
        for relative in _expand_manifest_entry_paths(entry, classes):
            primary = data_dir / relative
            if primary.exists():
                continue
            fallback = entry.get("fallback")
            if fallback and (data_dir / fallback).exists():
                continue
            missing.append(str(primary))
    return missing
