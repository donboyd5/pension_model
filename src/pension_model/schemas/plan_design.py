"""Schema for the ``plan_design`` block of plan_config.json."""

from __future__ import annotations

from pydantic import ConfigDict, Field, model_validator

from pension_model.schemas.base import StrictModel


class PlanDesignRatios(StrictModel):
    """Per-group benefit-type allocation ratios.

    Each per-group block describes how members are split across
    benefit types (DB / DC / CB), optionally with a before/after
    cutoff for the DB share. Field names match the keys consumed by
    ``PlanConfig.get_design_ratios``:

    - ``before_cutoff`` / ``after_cutoff``: DB share for entry years
      before/after the plan-design cutoff_year.
    - ``new`` / ``new_db``: DB share for new hires (entry_year >=
      ranges.new_year). ``new_db`` is the alias TXTRS uses.
    - ``before_cb`` / ``after_cb`` / ``new_cb``: CB shares.

    All fields optional; consumers default missing fields to 0.0 (CB)
    or fall through to ``new_db`` (DB).
    """

    before_cutoff: float | None = None
    after_cutoff: float | None = Field(
        default=None,
        description="Defaults to before_cutoff if omitted (no cutoff).",
    )
    new: float | None = None
    new_db: float | None = None
    before_cb: float | None = None
    after_cb: float | None = None
    new_cb: float | None = None
    new_dc: float | None = None

    def db_triple(self) -> tuple[float, float, float]:
        """Return ``(before, after, new)`` DB ratios with defaults
        applied: missing ``before_cutoff`` → 1.0, missing
        ``after_cutoff`` → ``before_cutoff``, missing ``new`` →
        ``new_db`` → 1.0.
        """
        before = self.before_cutoff if self.before_cutoff is not None else 1.0
        after = self.after_cutoff if self.after_cutoff is not None else before
        new = (
            self.new if self.new is not None else (self.new_db if self.new_db is not None else 1.0)
        )
        return (before, after, new)

    def cb_triple(self) -> tuple[float, float, float]:
        """Return ``(before, after, new)`` CB ratios with missing
        fields defaulting to 0.0.
        """
        return (
            self.before_cb if self.before_cb is not None else 0.0,
            self.after_cb if self.after_cb is not None else 0.0,
            self.new_cb if self.new_cb is not None else 0.0,
        )


class PlanDesign(StrictModel):
    """Top-level plan_design block.

    Has a fixed ``cutoff_year`` plus a variable-shape map of group
    name → :class:`PlanDesignRatios`. Group names depend on the
    plan's class_groups configuration (FRS uses ``regular_group`` /
    ``special_group``; TXTRS uses ``default``).

    Groups arrive in JSON as top-level keys; an ``after``-mode
    validator promotes each group's raw dict to a typed
    ``PlanDesignRatios`` instance and exposes them via the
    ``groups`` property.
    """

    # ``extra="allow"`` admits the per-group keys whose names depend
    # on the plan. Validation of the per-group payloads happens in
    # the after-validator below.
    model_config = ConfigDict(extra="allow", frozen=True)

    cutoff_year: int | None = None

    @model_validator(mode="after")
    def _promote_groups_to_typed_ratios(self) -> PlanDesign:
        """Convert each extra (group) entry to ``PlanDesignRatios``."""
        if not self.model_extra:
            return self
        promoted = {}
        for name, raw in self.model_extra.items():
            if isinstance(raw, PlanDesignRatios):
                promoted[name] = raw
            else:
                promoted[name] = PlanDesignRatios.model_validate(raw)
        # Re-set extras through the back door; pydantic stores extras
        # in __pydantic_extra__ on frozen models.
        object.__setattr__(self, "__pydantic_extra__", promoted)
        return self

    def group(self, name: str) -> PlanDesignRatios | None:
        """Look up a group's design ratios by name. Returns None if
        absent (caller decides whether to fall back to ``default``).
        """
        return (self.model_extra or {}).get(name)

    @property
    def groups(self) -> dict[str, PlanDesignRatios]:
        """All declared groups as a dict ``{name: PlanDesignRatios}``."""
        return dict(self.model_extra or {})
