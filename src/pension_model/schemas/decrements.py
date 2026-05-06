"""Schema for the ``decrements`` block of plan_config.json."""

from __future__ import annotations

from typing import Literal

from pension_model.schemas.base import StrictModel


class Decrements(StrictModel):
    """Decrement-method dispatch.

    Two supported methods, mapped to builders by
    ``data_loader._DECREMENT_BUILDERS``.
    """

    method: Literal["yos_only", "years_from_nr"]
