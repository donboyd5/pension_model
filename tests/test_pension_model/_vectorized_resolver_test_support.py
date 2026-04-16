"""Shared helpers for plan-specific vectorized resolver tests."""

import numpy as np


def build_frs_grid():
    """Dense grid of inputs covering FRS tier boundaries and class variations."""
    classes = ["regular", "special", "admin", "eco", "eso", "judges",
               "senior_management"]
    entry_years = [1970, 1990, 2000, 2010, 2011, 2015, 2020, 2021, 2022, 2025, 2030, 2040]
    ages = [20, 25, 30, 40, 50, 55, 58, 60, 62, 65, 68, 70, 75]
    yos_list = [0, 1, 5, 6, 8, 10, 15, 20, 25, 28, 30, 33, 35, 40]

    rows = []
    for cn in classes:
        for ey in entry_years:
            for age in ages:
                for yos in yos_list:
                    if age - yos >= 18 and age - yos <= age:
                        rows.append((cn, ey, age, yos))
    return rows


def build_txtrs_grid():
    """Grid for TXTRS covering grandfathering and tier boundaries."""
    classes = ["all"]
    entry_years = [1970, 1980, 1990, 1995, 2000, 2003, 2004, 2005, 2006,
                   2008, 2010, 2011, 2015, 2020, 2024, 2030]
    ages = [20, 25, 30, 40, 50, 55, 60, 62, 65, 70]
    yos_list = [0, 1, 5, 10, 15, 20, 25, 30, 35, 40]

    rows = []
    for cn in classes:
        for ey in entry_years:
            for age in ages:
                for yos in yos_list:
                    if age - yos >= 18:
                        rows.append((cn, ey, age, yos))
    return rows


def rows_to_arrays(rows):
    """Convert row tuples into NumPy arrays for vectorized resolver calls."""
    cn = np.array([r[0] for r in rows], dtype=object)
    ey = np.array([r[1] for r in rows], dtype=np.int64)
    age = np.array([r[2] for r in rows], dtype=np.int64)
    yos = np.array([r[3] for r in rows], dtype=np.int64)
    return cn, ey, age, yos


def scalar_cola(config, tier_str, entry_year, yos):
    """Reproduce the scalar COLA logic used by the annuity builder."""
    cola_cutoff = config.cola_proration_cutoff_year
    for td in config.tier_defs:
        if td["name"] in tier_str:
            cola_key = td.get("cola_key", "tier_1_active")
            raw_cola = config.cola.get(cola_key, 0.0)
            if (cola_key == "tier_1_active"
                    and not config.cola.get("tier_1_active_constant", False)
                    and cola_cutoff is not None
                    and raw_cola > 0 and yos > 0):
                yos_b4 = min(max(cola_cutoff - entry_year, 0), yos)
                return raw_cola * yos_b4 / yos
            return raw_cola
    return 0.0
