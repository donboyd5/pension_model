"""Compatibility adapters layered on top of ``PlanConfig``."""

from types import SimpleNamespace


def build_ranges_namespace(config) -> SimpleNamespace:
    return SimpleNamespace(
        min_age=config.min_age,
        max_age=config.max_age,
        start_year=config.start_year,
        new_year=config.new_year,
        min_entry_year=config.min_entry_year,
        model_period=config.model_period,
        max_yos=config.max_yos,
        max_entry_year=config.max_entry_year,
        entry_year_range=config.entry_year_range,
        age_range=config.age_range,
        yos_range=config.yos_range,
        max_year=config.max_year,
    )


def build_economic_namespace(config) -> SimpleNamespace:
    return SimpleNamespace(
        dr_current=config.dr_current,
        dr_new=config.dr_new,
        dr_old=config.dr_old,
        baseline_dr_current=config.baseline_dr_current,
        baseline_model_return=config.baseline_model_return,
        payroll_growth=config.payroll_growth,
        pop_growth=config.pop_growth,
        model_return=config.model_return,
        asset_return_path=config.asset_return_path,
    )


def build_benefit_namespace(config) -> SimpleNamespace:
    cola = config.cola
    return SimpleNamespace(
        db_ee_cont_rate=config.db_ee_cont_rate,
        db_ee_interest_rate=config.db_ee_interest_rate,
        cal_factor=config.cal_factor,
        retire_refund_ratio=config.retire_refund_ratio,
        cola_current_retire=cola.get("current_retire", 0.0),
        cola_current_retire_one=cola.get("current_retire_one_time", 0.0),
        one_time_cola=cola.get("one_time_cola", False),
    )


def build_funding_namespace(config) -> SimpleNamespace:
    return SimpleNamespace(
        funding_policy=config.funding_policy,
        contribution_strategy=config.contribution_strategy,
        amo_method=config.amo_method,
        amo_period_new=config.amo_period_new,
        amo_pay_growth=config.amo_pay_growth,
        funding_lag=config.funding_lag,
        amo_period_term=config.amo_period_term,
        amo_term_growth=config.amo_term_growth,
        ava_smoothing=config.ava_smoothing,
    )


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


