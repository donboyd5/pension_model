"""Lightweight runtime profiling helpers for the core pipeline."""

from __future__ import annotations

import json
import tracemalloc
import time
from dataclasses import dataclass
from pathlib import Path
from statistics import median

from pension_model.core.funding_model import load_funding_inputs, run_funding_model
from pension_model.core.pipeline import (
    PreparedPlanRun,
    prepare_plan_run,
    run_prepared_plan_pipeline,
    summarize_prepared_plan_run,
)


@dataclass(frozen=True)
class RuntimeProfile:
    """Timing summary for a plan run."""

    prepared_run: PreparedPlanRun
    liability_timing: float
    funding_timing: float | None
    prepare_peak_bytes: int
    liability_peak_bytes: int
    funding_peak_bytes: int | None

    @property
    def prepare(self) -> PreparedPlanRun:
        """Backward-compatible alias for the prepared runtime state."""
        return self.prepared_run

    @property
    def prepare_peak_mib(self) -> float:
        """Peak traced Python allocations during prepare, in MiB."""
        return self.prepare_peak_bytes / (1024 * 1024)

    @property
    def liability_peak_mib(self) -> float:
        """Peak traced Python allocations during liability, in MiB."""
        return self.liability_peak_bytes / (1024 * 1024)

    @property
    def funding_peak_mib(self) -> float | None:
        """Peak traced Python allocations during funding, in MiB."""
        if self.funding_peak_bytes is None:
            return None
        return self.funding_peak_bytes / (1024 * 1024)

    def as_dict(self) -> dict:
        summary = summarize_prepared_plan_run(self.prepared_run)
        summary["liability_timing"] = self.liability_timing
        summary["funding_timing"] = self.funding_timing
        summary["prepare_peak_bytes"] = self.prepare_peak_bytes
        summary["liability_peak_bytes"] = self.liability_peak_bytes
        summary["funding_peak_bytes"] = self.funding_peak_bytes
        return summary


def profile_runtime_sample(profile: RuntimeProfile) -> dict:
    """Return the portable timing/memory subset for one profile run."""
    summary = profile.as_dict()
    return {
        "stage_timings": dict(summary["stage_timings"]),
        "liability_timing": summary["liability_timing"],
        "funding_timing": summary["funding_timing"],
        "prepare_peak_bytes": summary["prepare_peak_bytes"],
        "liability_peak_bytes": summary["liability_peak_bytes"],
        "funding_peak_bytes": summary["funding_peak_bytes"],
    }


def _median_or_none(values: list[float | int | None]) -> float | int | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    med = median(present)
    return int(round(med)) if isinstance(present[0], int) else float(med)


def summarize_runtime_samples(samples: list[dict]) -> dict:
    """Summarize repeated runtime samples with stable median metrics."""
    if not samples:
        raise ValueError("summarize_runtime_samples() requires at least one sample")

    stage_names = tuple(samples[0]["stage_timings"].keys())
    return {
        "runs": len(samples),
        "stage_timings": {
            stage_name: float(median(sample["stage_timings"][stage_name] for sample in samples))
            for stage_name in stage_names
        },
        "liability_timing": float(median(sample["liability_timing"] for sample in samples)),
        "funding_timing": _median_or_none([sample["funding_timing"] for sample in samples]),
        "prepare_peak_bytes": _median_or_none([sample["prepare_peak_bytes"] for sample in samples]),
        "liability_peak_bytes": _median_or_none([sample["liability_peak_bytes"] for sample in samples]),
        "funding_peak_bytes": _median_or_none([sample["funding_peak_bytes"] for sample in samples]),
    }


def build_runtime_baseline(profiles_by_plan: dict[str, list[RuntimeProfile]]) -> dict:
    """Build a JSON-serializable runtime baseline from benchmark profiles."""
    baseline = {
        "schema_version": 1,
        "plans": {},
    }
    for plan_name, profiles in profiles_by_plan.items():
        if not profiles:
            continue
        samples = [profile_runtime_sample(profile) for profile in profiles]
        baseline["plans"][plan_name] = {
            "prepared_summary": summarize_prepared_plan_run(profiles[0].prepared_run),
            "runs": samples,
            "summary": summarize_runtime_samples(samples),
        }
    return baseline


def write_runtime_baseline(path: str | Path, baseline: dict) -> Path:
    """Write a runtime baseline JSON file."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n")
    return output_path


def load_runtime_baseline(path: str | Path) -> dict:
    """Load a runtime baseline JSON file."""
    return json.loads(Path(path).read_text())


def _metric_delta(current: float | int | None, baseline: float | int | None) -> dict:
    if current is None or baseline is None:
        return {
            "current": current,
            "baseline": baseline,
            "delta": None,
            "pct_delta": None,
        }
    delta = current - baseline
    pct_delta = None if baseline == 0 else delta / baseline
    return {
        "current": current,
        "baseline": baseline,
        "delta": delta,
        "pct_delta": pct_delta,
    }


def compare_runtime_baselines(current: dict, baseline: dict) -> dict:
    """Compare two runtime baseline documents."""
    comparison = {
        "schema_version": 1,
        "plans": {},
    }
    for plan_name, current_plan in current.get("plans", {}).items():
        baseline_plan = baseline.get("plans", {}).get(plan_name)
        if baseline_plan is None:
            continue

        current_summary = current_plan["summary"]
        baseline_summary = baseline_plan["summary"]
        comparison["plans"][plan_name] = {
            "stage_timings": {
                stage_name: _metric_delta(
                    current_summary["stage_timings"].get(stage_name),
                    baseline_summary["stage_timings"].get(stage_name),
                )
                for stage_name in current_summary["stage_timings"]
            },
            "liability_timing": _metric_delta(
                current_summary["liability_timing"],
                baseline_summary["liability_timing"],
            ),
            "funding_timing": _metric_delta(
                current_summary["funding_timing"],
                baseline_summary["funding_timing"],
            ),
            "prepare_peak_bytes": _metric_delta(
                current_summary["prepare_peak_bytes"],
                baseline_summary["prepare_peak_bytes"],
            ),
            "liability_peak_bytes": _metric_delta(
                current_summary["liability_peak_bytes"],
                baseline_summary["liability_peak_bytes"],
            ),
            "funding_peak_bytes": _metric_delta(
                current_summary["funding_peak_bytes"],
                baseline_summary["funding_peak_bytes"],
            ),
        }
    return comparison


def _profile_stage(func, *args, **kwargs):
    """Run one stage with elapsed time and traced peak Python allocations."""
    tracemalloc.start()
    try:
        started_at = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - started_at
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return result, elapsed, peak


def _run_funding_stage(prepared_run: PreparedPlanRun, liability: dict) -> dict:
    """Run the funding stage, including funding-input loading."""
    funding_inputs = load_funding_inputs(prepared_run.constants.resolve_data_dir() / "funding")
    return run_funding_model(liability, funding_inputs, prepared_run.constants)


def profile_plan_runtime(
    constants,
    *,
    include_funding: bool = False,
    research_mode: bool = False,
) -> RuntimeProfile:
    """Profile the prepare/liability/funding stages for a plan."""
    prepared_run, _, prepare_peak_bytes = _profile_stage(
        prepare_plan_run,
        constants,
        research_mode=research_mode,
    )

    liability, liability_timing, liability_peak_bytes = _profile_stage(
        run_prepared_plan_pipeline,
        prepared_run,
    )

    funding_timing = None
    funding_peak_bytes = None
    if include_funding:
        _, funding_timing, funding_peak_bytes = _profile_stage(
            _run_funding_stage,
            prepared_run,
            liability,
        )

    return RuntimeProfile(
        prepared_run=prepared_run,
        liability_timing=liability_timing,
        funding_timing=funding_timing,
        prepare_peak_bytes=prepare_peak_bytes,
        liability_peak_bytes=liability_peak_bytes,
        funding_peak_bytes=funding_peak_bytes,
    )
