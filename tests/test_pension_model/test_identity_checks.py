"""Funding identity assertion tests.

Two passing checks (FRS and TXTRS as run today) plus three synthetic
break tests that verify the checker raises with a clear message when
each identity is violated.
"""

from __future__ import annotations

import pytest

from pension_model.config_loading import load_plan_config_by_name
from pension_model.core._funding_setup import resolve_funding_context
from pension_model.core.funding_model import (
    load_funding_inputs,
    run_funding_model,
)
from pension_model.core.identity_checks import (
    IdentityCheckError,
    check_funding_identities,
)
from pension_model.core.pipeline import run_plan_pipeline


pytestmark = [pytest.mark.integration]


def _run_to_funding(plan_name: str):
    """Load plan, run liability + funding, return (funding, ctx)."""
    constants = load_plan_config_by_name(plan_name)
    liability = run_plan_pipeline(constants, progress=False)
    funding_inputs = load_funding_inputs(constants.resolve_data_dir() / "funding")
    funding = run_funding_model(liability, funding_inputs, constants)
    ctx = resolve_funding_context(constants, funding_inputs)
    return funding, ctx


@pytest.fixture(scope="module")
def txtrs_funding():
    return _run_to_funding("txtrs")


@pytest.fixture(scope="module")
def frs_funding():
    return _run_to_funding("frs")


def test_txtrs_identities_pass(txtrs_funding):
    funding, ctx = txtrs_funding
    check_funding_identities(
        funding,
        dr_current=ctx.dr_current,
        dr_new=ctx.dr_new,
        ret_scen=ctx.ret_scen,
        has_cb=ctx.has_cb,
        skip_classes={"drop"} if ctx.has_drop else set(),
    )


def test_frs_identities_pass(frs_funding):
    funding, ctx = frs_funding
    check_funding_identities(
        funding,
        dr_current=ctx.dr_current,
        dr_new=ctx.dr_new,
        ret_scen=ctx.ret_scen,
        has_cb=ctx.has_cb,
        skip_classes={"drop"} if ctx.has_drop else set(),
    )


def _perturb_copy(funding, class_name: str, column: str, row_index: int, delta: float):
    """Return a deep-copied funding dict with one cell perturbed."""
    perturbed = {cn: df.copy() for cn, df in funding.items()}
    perturbed[class_name].loc[row_index, column] = (
        perturbed[class_name].loc[row_index, column] + delta
    )
    return perturbed


def test_mva_break_is_caught(txtrs_funding):
    funding, ctx = txtrs_funding
    class_name = next(iter(funding))
    perturbed = _perturb_copy(funding, class_name, "mva_legacy", 5, 1e6)

    with pytest.raises(IdentityCheckError) as excinfo:
        check_funding_identities(
            perturbed,
            dr_current=ctx.dr_current, dr_new=ctx.dr_new,
            ret_scen=ctx.ret_scen, has_cb=ctx.has_cb,
            skip_classes={"drop"} if ctx.has_drop else set(),
        )

    msg = str(excinfo.value)
    assert "mva_rollforward" in msg
    # Perturbing row 5 breaks both year 5's check (actual vs expected)
    # and year 6's check (next year's expected uses perturbed value as
    # mva_prev). Either is acceptable evidence the check fired.
    violation_years = {v.year_index for v in excinfo.value.violations}
    assert {5, 6} & violation_years


def test_aal_break_is_caught(txtrs_funding):
    funding, ctx = txtrs_funding
    class_name = next(iter(funding))
    perturbed = _perturb_copy(funding, class_name, "aal_legacy", 7, 1e7)

    with pytest.raises(IdentityCheckError) as excinfo:
        check_funding_identities(
            perturbed,
            dr_current=ctx.dr_current, dr_new=ctx.dr_new,
            ret_scen=ctx.ret_scen, has_cb=ctx.has_cb,
            skip_classes={"drop"} if ctx.has_drop else set(),
        )

    msg = str(excinfo.value)
    assert "aal_rollforward" in msg


def test_nc_dollar_break_is_caught(txtrs_funding):
    funding, ctx = txtrs_funding
    class_name = next(iter(funding))
    perturbed = _perturb_copy(funding, class_name, "nc_legacy", 3, 5e5)

    with pytest.raises(IdentityCheckError) as excinfo:
        check_funding_identities(
            perturbed,
            dr_current=ctx.dr_current, dr_new=ctx.dr_new,
            ret_scen=ctx.ret_scen, has_cb=ctx.has_cb,
            skip_classes={"drop"} if ctx.has_drop else set(),
        )

    msg = str(excinfo.value)
    # NC dollar bug shows up first as an NC-dollar violation (perturbed
    # NC[3] no longer matches nc_rate × payroll), and downstream as an
    # AAL violation (next year's AAL roll uses the perturbed NC).
    assert "nc_dollar" in msg or "aal_rollforward" in msg
