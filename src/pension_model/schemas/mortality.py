"""Schema for the optional ``mortality`` section of plan_config.json.

TXTRS-style plans declare a single base mortality table for everyone.
FRS-style plans use the per-class ``base_table_map`` instead and don't
declare this section. Either pattern is fine; consumers that need a
class-specific table check ``base_table_map`` first and fall back to
``mortality.base_table``.
"""

from __future__ import annotations

from pension_model.schemas.base import StrictModel


class MortalitySpec(StrictModel):
    base_table: str = "general"
    improvement_scale: str | None = None
