"""Schema for the ``data`` section of plan_config.json.

Just one field today: where the plan's CSV inputs live. Kept as its
own model so future fields (URLs, version pins, alternate-source
toggles) can land in a typed home.
"""

from __future__ import annotations

from pension_model.schemas.base import StrictModel


class DataSpec(StrictModel):
    data_dir: str
