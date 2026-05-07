"""Schema for scenario JSON files (``scenarios/<name>.json``).

A scenario is a sparse override on a base plan config plus a little
metadata. The schema gives the override block typed validation so a
typo at any depth fails fast — previously ``_deep_merge`` would
silently create new keys and leave the user with results that looked
plausible but didn't reflect the scenario's intent.

Loader flow:

1. Load the scenario JSON, validate via :class:`Scenario`. Any unknown
   field at any depth in ``overrides`` raises here.
2. Optionally check ``requires`` against the loaded base plan (each
   path must resolve to a present, truthy field).
3. Deep-merge the (validated) override dict into the base raw plan
   config.
4. Re-validate the merged result as :class:`PlanConfig`. Any
   structural invariant the merge happens to violate fails here.

Step 1 catches typos; step 4 catches structurally illegal merged
results. Together they replace the old "merge whatever, hope for
the best" behavior.
"""

from __future__ import annotations

from pydantic import Field

from pension_model.config_schema import PlanConfig
from pension_model.schemas.base import StrictModel
from pension_model.schemas.partial import partial_model

# Recursive partial of PlanConfig. Built once at import; ``extra="forbid"``
# at the top level catches typos there (PlanConfig itself uses
# ``extra="ignore"`` to tolerate documentation keys).
ScenarioOverrides = partial_model(PlanConfig, extra="forbid")


class Scenario(StrictModel):
    """One scenario file (``scenarios/<name>.json``).

    ``overrides`` is the partial-typed delta applied to a base plan
    config. ``requires`` is an optional list of dotted paths into the
    base plan that must resolve to a truthy field for the scenario
    to apply — used to reject scenarios that target a feature the
    plan doesn't have (e.g., a "suspend DROP" scenario applied to a
    plan with no DROP configured).
    """

    name: str
    description: str = ""
    requires: list[str] = Field(default_factory=list)
    overrides: ScenarioOverrides  # type: ignore[valid-type]


def check_scenario_requires(plan: PlanConfig, requires: list[str]) -> None:
    """Verify each path in ``requires`` resolves to a truthy field
    on ``plan``. Raises ``ValueError`` listing the missing paths.

    Path syntax is dotted attribute access:
    ``"funding.has_drop"``, ``"economic.dr_old"``, etc. Each step
    uses ``getattr``; missing intermediate attributes count as
    "not present".
    """
    missing: list[str] = []
    for path in requires:
        obj: object = plan
        for part in path.split("."):
            obj = getattr(obj, part, None)
            if obj is None:
                break
        if not obj:
            missing.append(path)
    if missing:
        raise ValueError(
            f"Scenario requires plan features that are not present "
            f"or are falsy: {missing}. Either pick a different plan "
            f"or remove these from the scenario's 'requires' list."
        )
