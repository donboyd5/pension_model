"""Runtime assertion of funding-model identities.

The funding model's correctness depends on three identities holding to
floating-point precision (per ``meta-docs/pension_math.md``):

* **MVA roll-forward** —
  :func:`pension_model.core._funding_helpers._mva_rollforward`
  ``mva[i] = mva[i-1] * (1 + roa) + net_cf[i] * (1 + roa) ** 0.5``
* **AAL roll-forward** —
  :func:`pension_model.core._funding_helpers._aal_rollforward`
  ``aal[i] = aal[i-1] * (1 + dr) + (nc - ben - refund) * (1 + dr) ** 0.5 + liab_gl``
* **Normal-cost dollar identity** —
  ``nc_dollar = nc_rate * payroll`` per leg.

These identities are computed inline in
:mod:`pension_model.core._funding_phases` but never asserted. A bug
that breaks one (column rename, indexing slip, off-by-one) silently
produces numbers R also doesn't have, so the R-baseline test is no
longer load-bearing for that bug.

This module recomputes each identity from the funding frames and
raises :class:`IdentityCheckError` on the first violation above
tolerance. Off by default (zero cost on normal runs); enabled via the
``--check-identities`` CLI flag, which sets
:attr:`FundingContext.check_identities`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Optional

import numpy as np
import pandas as pd

from pension_model.core._funding_helpers import (
    _aal_rollforward,
    _mva_rollforward,
)


@dataclass
class IdentityViolation:
    """One residual that exceeded tolerance."""
    year_index: int
    class_name: str
    leg: str            # "legacy" or "new"
    identity: str       # "mva_rollforward", "aal_rollforward", "nc_dollar"
    expected: float
    actual: float
    residual: float


class IdentityCheckError(AssertionError):
    """A funding-model identity failed to hold to tolerance."""

    def __init__(self, violations: list[IdentityViolation]):
        self.violations = violations
        first = violations[0]
        n = len(violations)
        msg_lines = [
            f"{n} identity violation(s); first failure:",
            f"  year_index={first.year_index} class={first.class_name} "
            f"leg={first.leg} identity={first.identity}",
            f"  expected={first.expected!r}",
            f"  actual=  {first.actual!r}",
            f"  residual={first.residual!r}",
        ]
        if n > 1:
            msg_lines.append(
                f"  (and {n - 1} more — see ``IdentityCheckError.violations``)"
            )
        super().__init__("\n".join(msg_lines))


def _within_tol(residual: float, reference: float, tol_rel: float, tol_abs: float) -> bool:
    return (
        abs(residual) <= tol_abs
        or abs(residual) / max(1.0, abs(reference)) <= tol_rel
    )


def _check_mva_leg(
    f: pd.DataFrame, leg: str, ret_scen: pd.Series, class_name: str,
    tol_rel: float, tol_abs: float,
) -> Iterable[IdentityViolation]:
    mva_col = f"mva_{leg}"
    cf_col = f"net_cf_{leg}"
    if mva_col not in f.columns or cf_col not in f.columns:
        return
    years = f["year"].to_numpy()
    mva = f[mva_col].to_numpy()
    cf = f[cf_col].to_numpy()
    for i in range(1, len(f)):
        roa = float(ret_scen.loc[int(years[i])])
        expected = _mva_rollforward(mva[i - 1], cf[i], roa)
        actual = mva[i]
        residual = actual - expected
        if not _within_tol(residual, expected, tol_rel, tol_abs):
            yield IdentityViolation(
                year_index=i, class_name=class_name, leg=leg,
                identity="mva_rollforward",
                expected=expected, actual=actual, residual=residual,
            )


def _check_aal_leg(
    f: pd.DataFrame, leg: str, dr: float, class_name: str,
    tol_rel: float, tol_abs: float,
) -> Iterable[IdentityViolation]:
    aal_col = f"aal_{leg}"
    nc_col = f"nc_{leg}"
    ben_col = f"ben_payment_{leg}"
    refund_col = f"refund_{leg}"
    gl_col = f"liability_gain_loss_{leg}"
    needed = [aal_col, nc_col, ben_col, refund_col, gl_col]
    if not all(c in f.columns for c in needed):
        return
    aal = f[aal_col].to_numpy()
    nc = f[nc_col].to_numpy()
    ben = f[ben_col].to_numpy()
    refund = f[refund_col].to_numpy()
    gl = f[gl_col].to_numpy()
    for i in range(1, len(f)):
        expected = _aal_rollforward(
            aal_prev=aal[i - 1], nc=nc[i], ben=ben[i],
            refund=refund[i], liab_gl=gl[i], dr=dr,
        )
        actual = aal[i]
        residual = actual - expected
        if not _within_tol(residual, expected, tol_rel, tol_abs):
            yield IdentityViolation(
                year_index=i, class_name=class_name, leg=leg,
                identity="aal_rollforward",
                expected=expected, actual=actual, residual=residual,
            )


def _check_nc_dollar(
    f: pd.DataFrame, class_name: str, has_cb: bool,
    tol_rel: float, tol_abs: float,
) -> Iterable[IdentityViolation]:
    """``nc = nc_rate × payroll`` per leg.

    For ``new``, when the plan has a cash-balance leg, NC is the sum of
    the DB and CB contributions:
    ``nc_new = nc_rate_db_new * payroll_db_new + nc_rate_cb_new * payroll_cb_new``.
    """
    if {"nc_legacy", "nc_rate_db_legacy", "payroll_db_legacy"} <= set(f.columns):
        legacy_expected = (
            f["nc_rate_db_legacy"].to_numpy() * f["payroll_db_legacy"].to_numpy()
        )
        legacy_actual = f["nc_legacy"].to_numpy()
        for i in range(1, len(f)):
            residual = legacy_actual[i] - legacy_expected[i]
            if not _within_tol(residual, legacy_expected[i], tol_rel, tol_abs):
                yield IdentityViolation(
                    year_index=i, class_name=class_name, leg="legacy",
                    identity="nc_dollar",
                    expected=float(legacy_expected[i]),
                    actual=float(legacy_actual[i]),
                    residual=float(residual),
                )

    if {"nc_new", "nc_rate_db_new", "payroll_db_new"} <= set(f.columns):
        new_expected = (
            f["nc_rate_db_new"].to_numpy() * f["payroll_db_new"].to_numpy()
        )
        if has_cb and {"nc_rate_cb_new", "payroll_cb_new"} <= set(f.columns):
            new_expected = new_expected + (
                f["nc_rate_cb_new"].to_numpy() * f["payroll_cb_new"].to_numpy()
            )
        new_actual = f["nc_new"].to_numpy()
        for i in range(1, len(f)):
            residual = new_actual[i] - new_expected[i]
            if not _within_tol(residual, new_expected[i], tol_rel, tol_abs):
                yield IdentityViolation(
                    year_index=i, class_name=class_name, leg="new",
                    identity="nc_dollar",
                    expected=float(new_expected[i]),
                    actual=float(new_actual[i]),
                    residual=float(residual),
                )


def check_funding_identities(
    funding: Mapping[str, pd.DataFrame],
    *,
    dr_current: float,
    dr_new: float,
    ret_scen: pd.Series,
    has_cb: bool,
    skip_classes: Optional[set[str]] = None,
    tol_rel: float = 1e-9,
    tol_abs: float = 1e-3,
) -> None:
    """Recompute MVA, AAL, NC identities; raise on first violation.

    Parameters
    ----------
    funding:
        Dict of class-keyed funding frames returned by
        :func:`pension_model.core.funding_model.run_funding_model`.
    dr_current, dr_new:
        Discount rates used for the legacy and new legs.
    ret_scen:
        Series of asset returns by calendar year.
    has_cb:
        Whether the plan has a cash-balance leg (affects NC dollar
        composition for the ``new`` leg).
    skip_classes:
        Frame names to skip — e.g. ``{"drop"}`` for plans whose DROP
        overlay reallocates AVA across legs in a way that leaves the
        per-class identities intact but the synthetic frame's
        rollforward semantics different. The aggregate frame is
        always checked.
    tol_rel:
        Relative tolerance, applied as
        ``|residual| / max(1, |reference|)``.
    tol_abs:
        Absolute floor (dollars) for early-year cases where AAL or
        MVA is small.

    Raises
    ------
    IdentityCheckError
        On the first violation; ``.violations`` carries the full list
        found before the raise.
    """
    skip = skip_classes or set()
    violations: list[IdentityViolation] = []

    for class_name, frame in funding.items():
        if class_name in skip:
            continue
        if "year" not in frame.columns:
            continue
        for leg, dr in (("legacy", dr_current), ("new", dr_new)):
            violations.extend(
                _check_mva_leg(frame, leg, ret_scen, class_name, tol_rel, tol_abs)
            )
            violations.extend(
                _check_aal_leg(frame, leg, dr, class_name, tol_rel, tol_abs)
            )
        violations.extend(
            _check_nc_dollar(frame, class_name, has_cb, tol_rel, tol_abs)
        )

    if violations:
        raise IdentityCheckError(violations)
