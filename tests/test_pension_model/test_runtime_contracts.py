"""Prepared-run runtime-contract and profiling regression tests."""

import sys
from pathlib import Path

import pytest
from pandas.testing import assert_frame_equal

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pension_model.core.pipeline import (  # noqa: E402
    prepare_plan_run,
    run_plan_pipeline,
    run_prepared_plan_pipeline,
    summarize_prepared_plan_run,
)
from pension_model.core.profiling import (  # noqa: E402
    build_runtime_baseline,
    compare_runtime_baselines,
    load_runtime_baseline,
    profile_plan_runtime,
    summarize_runtime_samples,
    write_runtime_baseline,
)
from pension_model.core.runtime_contracts import ClassRuntimeTables  # noqa: E402
from pension_model.plan_config import load_plan_config_by_name  # noqa: E402

pytestmark = [pytest.mark.regression]


@pytest.fixture(scope="module")
def txtrs_constants():
    return load_plan_config_by_name("txtrs")


@pytest.fixture(scope="module")
def prepared_txtrs(txtrs_constants):
    return prepare_plan_run(txtrs_constants)


@pytest.fixture(scope="module")
def txtrs_profile(txtrs_constants):
    return profile_plan_runtime(txtrs_constants, include_funding=True)


def test_prepare_plan_run_returns_typed_runtime_tables(prepared_txtrs):
    runtime_tables = prepared_txtrs.runtime_tables_by_class["all"]
    assert isinstance(runtime_tables, ClassRuntimeTables)
    assert set(runtime_tables.as_dict()) == {
        "salary_headcount",
        "entrant_profile",
        "separation_rate",
        "benefit_val",
        "active_benefit_lookup",
        "term_liability_lookup",
        "benefit_decision_lookup",
        "refund_lookup",
        "retire_benefit_lookup",
        "retire_annuity_lookup",
        "current_retiree_liability",
        "current_term_vested_liability",
    }
    assert "entry_age" in runtime_tables.salary_headcount.columns
    assert "dist_age" in runtime_tables.benefit_decision_lookup.columns
    assert "year" in runtime_tables.term_liability_lookup.columns
    assert "dist_year" not in runtime_tables.term_liability_lookup.columns
    assert "retire_year" in runtime_tables.retire_benefit_lookup.columns
    assert "aal_retire_current_est" in runtime_tables.current_retiree_liability.columns
    assert "aal_term_current_est" in runtime_tables.current_term_vested_liability.columns


def test_summarize_prepared_plan_run_reports_runtime_table_rows(prepared_txtrs):
    summary = summarize_prepared_plan_run(prepared_txtrs)
    assert "runtime_table_rows" in summary
    runtime_rows = summary["runtime_table_rows"]["all"]
    assert runtime_rows["benefit_val"] > 0
    assert runtime_rows["active_benefit_lookup"] > 0
    assert runtime_rows["term_liability_lookup"] > 0
    assert runtime_rows["retire_annuity_lookup"] > 0
    assert runtime_rows["current_retiree_liability"] > 0
    assert runtime_rows["current_term_vested_liability"] > 0


def test_prepared_lookup_tables_keep_unique_merge_keys(prepared_txtrs):
    runtime_tables = prepared_txtrs.runtime_tables_by_class["all"]
    assert (
        runtime_tables.active_benefit_lookup.duplicated(["entry_year", "entry_age", "yos"]).sum()
        == 0
    )
    assert (
        runtime_tables.term_liability_lookup.duplicated(
            ["entry_age", "entry_year", "age", "year", "term_year"]
        ).sum()
        == 0
    )
    assert (
        runtime_tables.refund_lookup.duplicated(
            ["entry_age", "entry_year", "age", "year", "term_year"]
        ).sum()
        == 0
    )
    assert (
        runtime_tables.retire_benefit_lookup.duplicated(
            ["entry_age", "entry_year", "retire_year", "term_year"]
        ).sum()
        == 0
    )
    assert (
        runtime_tables.retire_annuity_lookup.duplicated(
            ["entry_age", "entry_year", "year", "term_year"]
        ).sum()
        == 0
    )


def test_prepared_pipeline_matches_direct_pipeline(txtrs_constants, prepared_txtrs):
    direct = run_plan_pipeline(txtrs_constants)
    prepared = run_prepared_plan_pipeline(prepared_txtrs)
    assert direct.keys() == prepared.keys()
    for class_name in direct:
        assert_frame_equal(direct[class_name], prepared[class_name], check_exact=True)


def test_profile_plan_runtime_reports_peak_memory(txtrs_profile):
    assert txtrs_profile.prepare_peak_bytes > 0
    assert txtrs_profile.liability_peak_bytes > 0
    assert txtrs_profile.funding_peak_bytes is not None
    assert txtrs_profile.funding_peak_bytes > 0

    summary = txtrs_profile.as_dict()
    assert summary["prepare_peak_bytes"] == txtrs_profile.prepare_peak_bytes
    assert summary["liability_peak_bytes"] == txtrs_profile.liability_peak_bytes
    assert summary["funding_peak_bytes"] == txtrs_profile.funding_peak_bytes


def test_runtime_baseline_helpers_round_trip(tmp_path, txtrs_profile):
    baseline = build_runtime_baseline({"txtrs": [txtrs_profile, txtrs_profile]})
    assert baseline["schema_version"] == 1
    assert baseline["plans"]["txtrs"]["summary"]["runs"] == 2

    summary = summarize_runtime_samples(baseline["plans"]["txtrs"]["runs"])
    assert summary == baseline["plans"]["txtrs"]["summary"]

    baseline_path = write_runtime_baseline(tmp_path / "runtime_baseline.json", baseline)
    loaded = load_runtime_baseline(baseline_path)
    assert loaded == baseline

    comparison = compare_runtime_baselines(loaded, baseline)
    plan_comparison = comparison["plans"]["txtrs"]
    assert plan_comparison["stage_timings"]["load_inputs"]["delta"] == pytest.approx(0.0)
    assert plan_comparison["liability_timing"]["delta"] == pytest.approx(0.0)
    assert plan_comparison["prepare_peak_bytes"]["delta"] == 0
