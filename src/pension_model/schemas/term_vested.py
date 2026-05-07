"""Schema for the ``term_vested`` section of plan_config.json.

Used only by data prep — the runtime reads ``current_term_vested_cashflow.csv``
and never consults this section. Kept here so prep scripts can validate
the same way the runtime config does.

Today this is TXTRS-AV only; other plans omit it.
"""

from __future__ import annotations

from typing import Literal

from pension_model.schemas.base import StrictModel


class TermVested(StrictModel):
    avg_deferral_years: int
    avg_payout_years: int
    method: Literal["deferred_annuity"]
    notes: str | None = None
