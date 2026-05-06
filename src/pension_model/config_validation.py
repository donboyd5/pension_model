"""Validation helpers for loaded plan configs."""

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

    for class_name, valuation in config.valuation_inputs.items():
        if "ben_payment" not in valuation:
            warnings.append(
                f"class '{class_name}' is missing 'ben_payment' in valuation_inputs. "
                f"This is the initial-year pension benefit payments to "
                f"current retirees (used to seed the retiree liability projection)."
            )

    for class_name, calibration in config.calibration.items():
        nc_cal = calibration.get("nc_cal", 1.0)
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

    if "dc" in config.benefit_types:
        for class_name in config.classes:
            if "er_dc_cont_rate" not in config.valuation_inputs.get(class_name, {}):
                warnings.append(
                    f"class '{class_name}' is missing 'er_dc_cont_rate' in valuation_inputs "
                    f"but benefit_types includes 'dc'."
                )

    for class_name, valuation in config.valuation_inputs.items():
        headcount_group = valuation.get("headcount_group")
        if headcount_group and len(headcount_group) > 1:
            target = valuation["total_active_member"]
            for peer in headcount_group:
                peer_target = config.valuation_inputs.get(peer, {}).get("total_active_member")
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
