"""
Pension Model Module

End-to-end pension model: raw inputs -> benefit tables -> liability -> funding.

Production modules:
- core.pipeline: Liability computation pipeline
- core.funding_model: Funding projection
- core.benefit_tables: Actuarial table construction
- core.tier_logic: Plan-specific tier and benefit rules
- core.model_constants: All model parameters
"""

from .core import run_class_pipeline, compute_funding, load_funding_inputs, frs_constants

__all__ = [
    "run_class_pipeline",
    "compute_funding",
    "load_funding_inputs",
    "frs_constants",
]
