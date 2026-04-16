"""FRS-specific unit tests for vectorized config resolvers."""

import numpy as np
import pandas as pd
import pytest

pytestmark = [pytest.mark.unit]

from pension_model.plan_config import (
    get_ben_mult,
    get_reduce_factor,
    get_tier,
    load_frs_config,
    resolve_ben_mult_vec,
    resolve_cola_vec,
    resolve_reduce_factor_vec,
    resolve_tiers_vec,
    resolve_tiers_vec_str,
)

from ._vectorized_resolver_test_support import (
    build_frs_grid,
    rows_to_arrays,
    scalar_cola,
)


def test_resolve_tiers_vec_matches_scalar_frs():
    config = load_frs_config()
    rows = build_frs_grid()
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


def test_resolve_tiers_vec_accepts_categorical_class_name():
    config = load_frs_config()
    rows = build_frs_grid()[:500]
    cn, ey, age, yos = rows_to_arrays(rows)

    expected_tier_id, expected_ret_status = resolve_tiers_vec(config, cn, ey, age, yos)
    actual_tier_id, actual_ret_status = resolve_tiers_vec(
        config, pd.Categorical(cn), ey, age, yos
    )

    assert np.array_equal(actual_tier_id, expected_tier_id)
    assert np.array_equal(actual_ret_status, expected_ret_status)


def test_resolve_tiers_vec_entry_age_override_frs():
    config = load_frs_config()
    cn = np.array(["regular", "regular"], dtype=object)
    ey = np.array([2000, 2000], dtype=np.int64)
    age = np.array([40, 40], dtype=np.int64)
    yos = np.array([10, 10], dtype=np.int64)
    ea_override = np.array([25, 0], dtype=np.int64)

    actual = resolve_tiers_vec_str(config, cn, ey, age, yos, entry_age=ea_override)
    expected = np.array([
        get_tier(config, "regular", 2000, 40, 10, entry_age=25),
        get_tier(config, "regular", 2000, 40, 10, entry_age=30),
    ], dtype=object)
    assert np.array_equal(actual, expected)


def test_resolve_cola_vec_matches_scalar_frs():
    config = load_frs_config()
    rows = build_frs_grid()
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


def test_resolve_ben_mult_vec_matches_scalar_frs():
    config = load_frs_config()
    rows = build_frs_grid()
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


def test_resolve_ben_mult_vec_accepts_categorical_class_name():
    config = load_frs_config()
    rows = build_frs_grid()[:500]
    cn, ey, age, yos = rows_to_arrays(rows)
    tier_id, ret_status = resolve_tiers_vec(config, cn, ey, age, yos)
    dist_year = ey + yos

    expected = resolve_ben_mult_vec(
        config, cn, tier_id, ret_status, age, yos, dist_year
    )
    actual = resolve_ben_mult_vec(
        config, pd.Categorical(cn), tier_id, ret_status, age, yos, dist_year
    )

    assert np.allclose(actual, expected, equal_nan=True)


def test_resolve_reduce_factor_vec_matches_scalar_frs():
    config = load_frs_config()
    rows = build_frs_grid()
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


def test_resolve_reduce_factor_vec_accepts_categorical_class_name():
    config = load_frs_config()
    rows = build_frs_grid()[:500]
    cn, ey, age, yos = rows_to_arrays(rows)
    tier_id, ret_status = resolve_tiers_vec(config, cn, ey, age, yos)

    expected = resolve_reduce_factor_vec(config, cn, tier_id, ret_status, age, yos, ey)
    actual = resolve_reduce_factor_vec(
        config, pd.Categorical(cn), tier_id, ret_status, age, yos, ey
    )

    nan_match = np.isnan(expected) == np.isnan(actual)
    val_match = np.where(
        np.isnan(expected), True, np.isclose(actual, expected, equal_nan=True)
    )
    assert np.all(nan_match & val_match)
