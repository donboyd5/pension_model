"""Schema for the ``ranges`` block of plan_config.json."""

from __future__ import annotations

from pydantic import Field, model_validator

from pension_model.schemas.base import StrictModel


class Ranges(StrictModel):
    """Year/age/YOS bounds for the simulation. Derived ranges
    (``entry_year_range``, ``age_range``, ``yos_range``,
    ``max_year``, ``max_entry_year``) are computed properties."""

    min_age: int
    max_age: int
    start_year: int
    new_year: int | None = Field(
        default=None,
        description="Year boundary that separates legacy hires from "
        "new hires. Defaults to start_year if omitted.",
    )
    min_entry_year: int = 1970
    model_period: int
    max_yos: int = 70

    @model_validator(mode="after")
    def _default_new_year(self) -> Ranges:
        if self.new_year is None:
            object.__setattr__(self, "new_year", self.start_year)
        return self

    @property
    def max_entry_year(self) -> int:
        return self.start_year + self.model_period

    @property
    def entry_year_range(self) -> range:
        return range(self.min_entry_year, self.max_entry_year + 1)

    @property
    def age_range(self) -> range:
        return range(self.min_age, self.max_age + 1)

    @property
    def yos_range(self) -> range:
        return range(0, self.max_yos + 1)

    @property
    def max_year(self) -> int:
        return self.start_year + self.model_period + self.max_age - self.min_age
