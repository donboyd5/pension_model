#!/usr/bin/env python
"""
CLI entry point for the pension model.

Usage:
    pension-model frs              # run FRS model + tests
    pension-model frs --no-test    # run FRS model only
    pension-model frs --test-only  # tests only (no model run)
"""

import sys
import time
import argparse
import warnings
from pathlib import Path


BASELINE = Path("baseline_outputs")
CLASSES = ["regular", "special", "admin", "eco", "eso", "judges", "senior_management"]


def run_pipeline(e2e=True):
    """Run liability + funding pipeline for all groups."""
    from pension_model.core.pipeline import run_class_pipeline, run_class_pipeline_e2e
    from pension_model.core.funding_model import load_funding_inputs, compute_funding
    from pension_model.core.model_constants import frs_constants

    constants = frs_constants()
    pipeline_fn = run_class_pipeline_e2e if e2e else run_class_pipeline

    n = len(CLASSES)
    liability = {}

    print("  Building benefit tables, workforce, and liabilities (this may take a while)...")
    for i, cn in enumerate(CLASSES):
        pct = int(i / n * 100)
        sys.stdout.write(f"\r    {pct:3d}%")
        sys.stdout.flush()
        liability[cn] = pipeline_fn(cn, BASELINE, constants)
    sys.stdout.write(f"\r    100% done\n")
    sys.stdout.flush()

    print("  Computing funding...")
    funding_inputs = load_funding_inputs(BASELINE)
    funding = compute_funding(liability, funding_inputs, constants)
    print("  Done.")

    return liability, funding


def run_tests():
    """Run all baseline validation and unit tests via pytest."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_pension_model/", "-v", "--tb=short"],
    )
    return result.returncode == 0


def cmd_frs(args):
    """Run the Florida FRS pension model."""
    if args.test_only:
        print("Running tests...")
        ok = run_tests()
        sys.exit(0 if ok else 1)

    print("=" * 60)
    print("FRS Pension Model Pipeline")
    print("=" * 60)

    t0 = time.time()
    liability, funding = run_pipeline()
    elapsed = time.time() - t0
    print(f"  Pipeline complete: {elapsed:.0f}s")

    if not args.no_test:
        print("\nRunning tests...")
        tests_ok = run_tests()
        sys.exit(0 if tests_ok else 1)


def main():
    warnings.filterwarnings("ignore")

    parser = argparse.ArgumentParser(description="Pension model CLI")
    subparsers = parser.add_subparsers(dest="plan", help="Plan to run")

    frs = subparsers.add_parser("frs", help="Florida Retirement System")
    frs.add_argument("--no-test", action="store_true", help="Skip tests")
    frs.add_argument("--test-only", action="store_true", help="Run tests only")

    args = parser.parse_args()

    if args.plan is None:
        parser.print_help()
        sys.exit(1)

    if args.plan == "frs":
        cmd_frs(args)
