"""Schema for the ``modeling`` block of plan_config.json."""

from __future__ import annotations

from pension_model.schemas.base import StrictModel


class AgeGroup(StrictModel):
    """One age band used by YOS-only termination-rate tables.

    Either ``min_age`` or ``max_age`` (or both) may be omitted to
    mean open-ended. ``label`` is the column name in the wide-format
    term_rate_avg table.
    """

    label: str
    min_age: int | None = None
    max_age: int | None = None


class Modeling(StrictModel):
    """Model-implementation knobs and modeling assumptions.

    Mixes actuarial choices (``use_earliest_retire``, ``age_groups``)
    with implementation knobs (``entrant_salary_at_start_year``,
    ``male_mp_forward_shift``). A future refactor should split these
    into two namespaces; for now they live together because
    plan_config.json organizes them that way.
    """

    entrant_salary_at_start_year: bool = False
    use_earliest_retire: bool = False
    male_mp_forward_shift: int = 0
    age_groups: list[AgeGroup] | None = None
