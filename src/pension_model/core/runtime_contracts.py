"""Typed runtime contracts for prepared liability runs."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True, slots=True)
class ClassRuntimeTables:
    """Per-class runtime tables consumed by the liability pipeline."""

    salary_headcount: pd.DataFrame
    entrant_profile: pd.DataFrame
    separation_rate: pd.DataFrame
    benefit_val: pd.DataFrame
    active_benefit_lookup: pd.DataFrame
    term_liability_lookup: pd.DataFrame
    benefit_decision_lookup: pd.DataFrame
    refund_lookup: pd.DataFrame
    retire_benefit_lookup: pd.DataFrame
    retire_annuity_lookup: pd.DataFrame
    current_retiree_liability: pd.DataFrame
    current_term_vested_liability: pd.DataFrame

    def as_dict(self) -> dict[str, pd.DataFrame]:
        """Return the tables as a name-keyed mapping."""
        return {
            "salary_headcount": self.salary_headcount,
            "entrant_profile": self.entrant_profile,
            "separation_rate": self.separation_rate,
            "benefit_val": self.benefit_val,
            "active_benefit_lookup": self.active_benefit_lookup,
            "term_liability_lookup": self.term_liability_lookup,
            "benefit_decision_lookup": self.benefit_decision_lookup,
            "refund_lookup": self.refund_lookup,
            "retire_benefit_lookup": self.retire_benefit_lookup,
            "retire_annuity_lookup": self.retire_annuity_lookup,
            "current_retiree_liability": self.current_retiree_liability,
            "current_term_vested_liability": self.current_term_vested_liability,
        }

    def row_counts(self) -> dict[str, int]:
        """Return row counts for the contained runtime tables."""
        return {name: len(frame) for name, frame in self.as_dict().items()}
