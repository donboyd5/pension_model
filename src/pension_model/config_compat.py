"""Compatibility adapters layered on top of ``PlanConfig``.

Per-class data still uses a ``SimpleNamespace`` builder; the migration
to typed pydantic models is in progress — see
``scratch/pydantic_migration_plan.md``.
"""

from types import SimpleNamespace


def build_class_data_namespace(config) -> dict:
    result = {}
    for class_name, valuation in config.valuation_inputs.items():
        calibration = config.calibration.get(class_name, {})
        result[class_name] = SimpleNamespace(
            ben_payment=valuation["ben_payment"],
            retiree_pop=valuation["retiree_pop"],
            total_active_member=valuation["total_active_member"],
            er_dc_cont_rate=valuation["er_dc_cont_rate"],
            val_norm_cost=valuation["val_norm_cost"],
            nc_cal=calibration.get("nc_cal", 1.0),
            pvfb_term_current=calibration.get("pvfb_term_current", 0.0),
        )
    return result


