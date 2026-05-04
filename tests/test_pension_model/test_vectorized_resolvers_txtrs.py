"""TXTRS-specific unit tests for vectorized config resolvers."""

import numpy as np
import pytest

pytestmark = [pytest.mark.unit]

from pension_model.plan_config import (
    get_ben_mult,
    get_reduce_factor,
    get_tier,
    load_plan_config_by_name,
    resolve_ben_mult_vec,
    resolve_cola_vec,
    resolve_reduce_factor_vec,
    resolve_tiers_vec,
    resolve_tiers_vec_str,
)

from ._vectorized_resolver_test_support import (
    build_txtrs_grid,
    rows_to_arrays,
    scalar_cola,
)


def test_resolve_tiers_vec_matches_scalar_txtrs():
    config = load_plan_config_by_name("txtrs")
    rows = build_txtrs_grid()
    cn, ey, age, yos = rows_to_arrays(rows)

    expected = np.array([
        get_tier(config, rows[i][0], int(ey[i]), int(age[i]), int(yos[i]))
        for i in range(len(rows))
    ], dtype=object)

    actual = resolve_tiers_vec_str(config, cn, ey, age, yos)

    mismatches = np.where(expected != actual)[0]
    if len(mismatches) > 0:
        diffs = [
            (rows[i], expected[i], actual[i])
            for i in mismatches[:10]
        ]
        pytest.fail(
            f"{len(mismatches)} / {len(rows)} mismatches. First 10: {diffs}"
        )


def test_resolve_cola_vec_matches_scalar_txtrs():
    config = load_plan_config_by_name("txtrs")
    rows = build_txtrs_grid()
    cn, ey, age, yos = rows_to_arrays(rows)

    tiers_str = resolve_tiers_vec_str(config, cn, ey, age, yos)
    tier_id, _ = resolve_tiers_vec(config, cn, ey, age, yos)

    expected = np.array([
        scalar_cola(config, tiers_str[i], int(ey[i]), int(yos[i]))
        for i in range(len(rows))
    ], dtype=np.float64)

    actual = resolve_cola_vec(config, tier_id, ey, yos)

    assert np.allclose(actual, expected, equal_nan=True), \
        f"COLA mismatch. Max diff: {np.nanmax(np.abs(actual - expected))}"


def test_resolve_ben_mult_vec_matches_scalar_txtrs():
    config = load_plan_config_by_name("txtrs")
    rows = build_txtrs_grid()
    cn, ey, age, yos = rows_to_arrays(rows)

    tiers_str = resolve_tiers_vec_str(config, cn, ey, age, yos)
    tier_id, ret_status = resolve_tiers_vec(config, cn, ey, age, yos)
    dist_year = ey + yos

    expected = np.array([
        get_ben_mult(config, rows[i][0], tiers_str[i], int(age[i]), int(yos[i]),
                     int(dist_year[i]))
        for i in range(len(rows))
    ], dtype=np.float64)

    actual = resolve_ben_mult_vec(config, cn, tier_id, ret_status, age, yos, dist_year)

    assert np.allclose(actual, expected, equal_nan=True), \
        f"ben_mult mismatch. Max diff: {np.nanmax(np.abs(actual - expected))}"


def test_resolve_reduce_factor_vec_matches_scalar_txtrs():
    config = load_plan_config_by_name("txtrs")
    rows = build_txtrs_grid()
    cn, ey, age, yos = rows_to_arrays(rows)

    tiers = resolve_tiers_vec_str(config, cn, ey, age, yos)
    tier_id, ret_status = resolve_tiers_vec(config, cn, ey, age, yos)

    expected = np.array([
        get_reduce_factor(config, rows[i][0], tiers[i], int(age[i]),
                          int(yos[i]), int(ey[i]))
        for i in range(len(rows))
    ], dtype=np.float64)

    actual = resolve_reduce_factor_vec(config, cn, tier_id, ret_status, age, yos, ey)

    nan_match = np.isnan(expected) == np.isnan(actual)
    val_match = np.where(np.isnan(expected), True,
                         np.isclose(actual, expected, equal_nan=True))
    mismatches = np.where(~(nan_match & val_match))[0]
    if len(mismatches) > 0:
        diffs = [
            (rows[i], tiers[i], expected[i], actual[i])
            for i in mismatches[:10]
        ]
        pytest.fail(
            f"{len(mismatches)} / {len(rows)} reduce_factor mismatches. "
            f"First 10: {diffs}"
        )
