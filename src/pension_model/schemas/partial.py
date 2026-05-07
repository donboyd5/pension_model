"""Recursive partial-model helper for scenario overrides.

A "partial" of a pydantic model is a model with the same field names
but every field made ``Optional[...] = None``. Nested ``BaseModel``
fields recurse — their partial is generated and substituted, so a
caller can override exactly one nested leaf field without having to
rebuild the surrounding sub-models.

Intended consumer: :class:`pension_model.schemas.scenario.ScenarioOverrides`,
which validates the ``overrides`` block of a scenario JSON. The
override dict gets type-checked at scenario load (catching typos and
references to non-existent fields), then ``_deep_merge``'d into the
raw plan_config dict, then re-validated as a full :class:`PlanConfig`.

Design notes:

* **Sub-model ``extra`` config is preserved.** ``Cola`` uses
  ``extra="allow"`` to admit per-tier active-rate keys; the partial
  must do the same so a ``no_cola``-style override doesn't fail on
  ``tier_3_active``.
* **Top-level ``extra`` is overridden to ``"forbid"``.** The whole
  point of typing scenario overrides is to catch typos at the top
  level (where ``PlanConfig`` itself uses ``extra="ignore"`` to
  tolerate documentation keys).
* **Validators are NOT inherited.** Sub-model validators (e.g.,
  ``EarlyRetireReduction`` requires either flat or rule-list shape)
  are meant for the *merged* result, not the override. Inheriting
  them would force scenarios to provide both shapes' fields together.
* **Generic containers don't recurse.** ``list[Tier]`` / ``dict[str,
  ValuationInputs]`` partial fields keep the full inner type — a
  scenario that overrides ``tier_defs`` provides complete tiers, not
  partials. None of today's scenarios do this; revisit if a use
  case appears.
"""

from __future__ import annotations

import types
from typing import Any, Optional, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, Field, create_model


def partial_model(
    cls: type[BaseModel],
    *,
    extra: Optional[str] = None,
    _cache: Optional[dict[type[BaseModel], type[BaseModel]]] = None,
) -> type[BaseModel]:
    """Build a recursive partial of ``cls``.

    Every field becomes ``Optional[...] = None``. Direct ``BaseModel``
    fields (and ``BaseModel`` args inside ``Union[...]``) recurse into
    their own partials. Other annotations (lists, dicts, primitives)
    pass through.

    Args:
        cls: pydantic model class to partialize.
        extra: when set, overrides the resulting model's ``extra`` config
            (use ``"forbid"`` for the top-level ``ScenarioOverrides``
            so unknown top-level keys fail). When ``None``, the
            partial inherits ``cls.model_config["extra"]``.

    Returns:
        A new pydantic ``BaseModel`` subclass with the partial schema.
        Cached on second call so recursive references don't loop.
    """
    if _cache is None:
        _cache = {}
    if cls in _cache:
        return _cache[cls]

    fields: dict[str, tuple[Any, Any]] = {}
    for name, field_info in cls.model_fields.items():
        partial_ann = _partialize_annotation(field_info.annotation, _cache)
        kwargs: dict[str, Any] = {"default": None}
        if field_info.alias is not None:
            kwargs["alias"] = field_info.alias
        fields[name] = (Optional[partial_ann], Field(**kwargs))

    parent_extra = (cls.model_config or {}).get("extra", "ignore")
    final_extra = extra if extra is not None else parent_extra
    new_config = ConfigDict(
        extra=final_extra,
        frozen=True,
        populate_by_name=True,
    )

    partial_cls = create_model(
        f"{cls.__name__}Partial",
        __base__=BaseModel,
        __config__=new_config,
        **fields,
    )
    _cache[cls] = partial_cls
    return partial_cls


def _partialize_annotation(
    annotation: Any,
    cache: dict[type[BaseModel], type[BaseModel]],
) -> Any:
    """Walk an annotation; recursively partialize ``BaseModel`` types."""
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return partial_model(annotation, _cache=cache)

    origin = get_origin(annotation)
    if origin is Union or origin is types.UnionType:
        new_args = tuple(_partialize_annotation(a, cache) for a in get_args(annotation))
        return Union[new_args]  # type: ignore[return-value]

    return annotation
