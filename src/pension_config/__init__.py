"""
pension_config module

Configuration management for pension modeling.

Active modules:
- types: Core enums (MembershipClass, Tier, FundingPolicy, etc.)
- plan: PlanConfig dataclass with FRS defaults
- adapters: PlanAdapter protocol for multi-plan support
- frs_adapter: FRS-specific adapter implementation
"""

from .types import MembershipClass, Tier, FundingPolicy, AmortizationMethod, ReturnScenario

__all__ = [
    "MembershipClass",
    "Tier",
    "FundingPolicy",
    "AmortizationMethod",
    "ReturnScenario",
]
