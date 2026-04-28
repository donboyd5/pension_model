#!/usr/bin/env python3
"""Build txtrs-av runtime funding/return_scenarios.csv.

This is a modeling-choice artifact, not document-sourced. The runtime
overrides the `model` and `assumption` columns with values from
plan_config.json (model_return and dr_current), so those columns are
nominal placeholders. The real content is the three stress scenarios:

  recession:        one near-term recession (year 1 = start_year)
  recur_recession:  two recessions ~15 years apart
  constant_6:       flat 6% reference

The recession shape mirrors the legacy txtrs convention:
  year 0 (= start_year - 1): no shock, long-term rate
  year 1 (= start_year):     recession (-24%)
  years 2-4:                 recovery (+11%)
  years 5-15:                post-recession steady state (+6%)
  year 16:                   second recession in recur_recession only
  years 17-19:               recovery in recur_recession
  years 20+:                 post-recession steady state

The horizon is 100 rows starting one year before start_year, matching the
legacy txtrs file length and pre-roll convention.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_PATH = PROJECT_ROOT / "plans" / "txtrs-av" / "data" / "funding" / "return_scenarios.csv"

START_YEAR = 2024            # txtrs-av plan_config.json ranges.start_year
LONG_TERM_RETURN = 0.07      # txtrs-av plan_config.json economic.model_return
POST_RECESSION_RATE = 0.06   # legacy long-term post-shock rate convention
RECESSION_RATE = -0.24
RECOVERY_RATE = 0.11
CONSTANT_6 = 0.06

HORIZON_YEARS = 100
FILE_START_YEAR = START_YEAR - 1

RECESSION_OFFSET = 1
RECOVERY_OFFSETS = (2, 3, 4)
RECUR_RECESSION_OFFSET = 16
RECUR_RECOVERY_OFFSETS = (17, 18, 19)


def _scenario_value(offset: int, second_only: bool) -> float:
    """Return scenario rate for a given year offset.

    second_only=True returns the recur_recession path (which adds the
    second shock at offset 16); False returns the basic recession path.
    """
    if offset == 0:
        return LONG_TERM_RETURN
    if offset == RECESSION_OFFSET:
        return RECESSION_RATE
    if offset in RECOVERY_OFFSETS:
        return RECOVERY_RATE
    if second_only and offset == RECUR_RECESSION_OFFSET:
        return RECESSION_RATE
    if second_only and offset in RECUR_RECOVERY_OFFSETS:
        return RECOVERY_RATE
    return POST_RECESSION_RATE


def build_return_scenarios() -> pd.DataFrame:
    rows: list[dict] = []
    for offset in range(HORIZON_YEARS):
        year = FILE_START_YEAR + offset
        rows.append({
            "year": year,
            "model": LONG_TERM_RETURN,
            "assumption": LONG_TERM_RETURN,
            "recession": _scenario_value(offset, second_only=False),
            "recur_recession": _scenario_value(offset, second_only=True),
            "constant_6": CONSTANT_6,
        })
    return pd.DataFrame(rows)


def main() -> None:
    df = build_return_scenarios()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"Wrote {OUT_PATH} ({len(df)} rows)")


if __name__ == "__main__":
    main()
