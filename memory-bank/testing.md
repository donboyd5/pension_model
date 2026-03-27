# R Model Comparison Testing

## Overview

This document tracks the comparison between Python implementation outputs and the original R model results. Each component must be validated before moving to the next phase.

---

## Test Data Sources

### R Model Reference Outputs
| File | Description | Status |
|------|-------------|--------|
| `R_model/R_model_original/*.rds` | RDS files from workforce model runs | [ ] Extracted |
| `baseline_outputs/` | Baseline outputs from R model | [ ] To be created |

### Input Data Files (Excel)
| File | Description | Python Status |
|------|-------------|---------------|
| `Florida FRS inputs.xlsx` | Main input file | [ ] Loaded |
| `Florida FRS COLA analysis.xlsx` | COLA scenarios | [ ] Loaded |
| `salary increase.xlsx` | Salary growth rates | [ ] Loaded |
| `withdrawal rate *.xlsx` | Withdrawal tables by tier | [ ] Loaded |
| `normal retirement tier *.xlsx` | Retirement eligibility | [ ] Loaded |
| `early retirement tier *.xlsx` | Early retirement factors | [ ] Loaded |
| `pub-2010-headcount-mort-rates.xlsx` | Mortality tables | [ ] Loaded |
| `mortality-improvement-scale-mp-2018-rates.xlsx` | Mortality improvement | [ ] Loaded |

---

## Component Validation Log

### pension_tools Module

#### Financial Functions
| Test Case | R Output | Python Output | Difference | Status |
|-----------|----------|---------------|------------|--------|
| PV(rate=0.067, nper=30, pmt=1000) | - | - | - | [ ] Not started |
| NPV(rate=0.067, cashflows) | - | - | - | [ ] Not started |
| FV(rate=0.067, nper=30, pmt=1000) | - | - | - | [ ] Not started |
| Discount factor at age 65 | - | - | - | [ ] Not started |

#### Salary Growth Functions
| Test Case | R Output | Python Output | Difference | Status |
|-----------|----------|---------------|------------|--------|
| Entry age 25, YOS 5 | - | - | - | [ ] Not started |
| Entry age 30, YOS 10 | - | - | - | [ ] Not started |
| Entry age 35, YOS 20 | - | - | - | [ ] Not started |

#### Mortality Calculations
| Test Case | R Output | Python Output | Difference | Status |
|-----------|----------|---------------|------------|--------|
| qx at age 65, male | - | - | - | [ ] Not started |
| qx at age 65, female | - | - | - | [ ] Not started |
| Mortality improvement | - | - | - | [ ] Not started |

#### Withdrawal Rates
| Test Case | R Output | Python Output | Difference | Status |
|-----------|----------|---------------|------------|--------|
| Admin, YOS 5, age 30 | - | - | - | [ ] Not started |
| Special Risk, YOS 10 | - | - | - | [ ] Not started |

#### Retirement Eligibility
| Test Case | R Output | Python Output | Difference | Status |
|-----------|----------|---------------|------------|--------|
| Tier 1 normal retirement | - | - | - | [ ] Not started |
| Tier 2 normal retirement | - | - | - | [ ] Not started |
| Early retirement factor | - | - | - | [ ] Not started |

#### Benefit Calculations
| Test Case | R Output | Python Output | Difference | Status |
|-----------|----------|---------------|------------|--------|
| Normal cost calculation | - | - | - | [ ] Not started |
| Accrued liability | - | - | - | [ ] Not started |
| Benefit multiplier application | - | - | - | [ ] Not started |

#### Amortization Calculations
| Test Case | R Output | Python Output | Difference | Status |
|-----------|----------|---------------|------------|--------|
| Amortization payment | - | - | - | [ ] Not started |
| Funding period NPER | - | - | - | [ ] Not started |

---

### pension_model Module

#### Workforce Projections
| Metric | R Output | Python Output | Difference | Status |
|--------|----------|---------------|------------|--------|
| Total headcount Year 1 | - | - | - | [ ] Not started |
| New entrants Year 1 | - | - | - | [ ] Not started |
| Terminations Year 1 | - | - | - | [ ] Not started |
| Retirements Year 1 | - | - | - | [ ] Not started |
| Active population by age | - | - | - | [ ] Not started |

#### Liability Calculations
| Metric | R Output | Python Output | Difference | Status |
|--------|----------|---------------|------------|--------|
| Total Actuarial Liability | - | - | - | [ ] Not started |
| Normal Cost | - | - | - | [ ] Not started |
| Present Value of Benefits | - | - | - | [ ] Not started |
| Liability by membership class | - | - | - | [ ] Not started |

#### Funding Calculations
| Metric | R Output | Python Output | Difference | Status |
|--------|----------|---------------|------------|--------|
| Required contribution | - | - | - | [ ] Not started |
| Amortization payment | - | - | - | [ ] Not started |
| Funded ratio | - | - | - | [ ] Not started |
| UAAL (Unfunded Actuarial Liability) | - | - | - | [ ] Not started |

#### COLA Calculations
| Metric | R Output | Python Output | Difference | Status |
|--------|----------|---------------|------------|--------|
| COLA adjustment tier 1 | - | - | - | [ ] Not started |
| COLA adjustment tier 2 | - | - | - | [ ] Not started |
| One-time COLA | - | - | - | [ ] Not started |

---

### Integration Tests

#### End-to-End Comparison
| Metric | R Output | Python Output | Difference | Status |
|--------|----------|---------------|------------|--------|
| Total liability Year 1 | - | - | - | [ ] Not started |
| Total liability Year 30 | - | - | - | [ ] Not started |
| Total contributions Year 1 | - | - | - | [ ] Not started |
| Total benefits paid Year 1 | - | - | - | [ ] Not started |
| Funded status Year 1 | - | - | - | [ ] Not started |
| Funded status Year 30 | - | - | - | [ ] Not started |

---

## Tolerance Thresholds

| Metric Type | Acceptable Difference | Notes |
|-------------|----------------------|-------|
| Counts (headcount) | ±1 (exact match expected) | Integer values |
| Rates | ±0.0001 (0.01%) | Decimal values |
| Currency | ±$1,000 or 0.1% | Whichever is larger |
| Present Values | ±0.1% | Large values |
| Percentages | ±0.01% | Small differences acceptable |

---

## Test Execution Commands

```bash
# Run all unit tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=pension_model --cov-report=html

# Run specific module tests
pytest tests/test_pension_tools/ -v
pytest tests/test_pension_model/ -v

# Run integration tests
pytest tests/test_integration/ -v

# Run with verbose output
pytest tests/ -vv --tb=short

# Run only tests that match a pattern
pytest tests/ -k "salary_growth" -v
```

---

## Test Fixtures

### Baseline R Outputs
The following R outputs will be captured as test fixtures:

```bash
# Run this to generate baseline outputs
Rscript scripts/extract_baseline.R
```

Fixtures will be saved in `tests/fixtures/baseline/`:
- `workforce_data.json` - Workforce projections
- `liability_data.json` - Liability calculations
- `funding_data.json` - Funding calculations
- `benefit_data.json` - Benefit calculations

---

## Issues Log

| Date | Component | Issue | R Value | Python Value | Difference | Status |
|------|-----------|-------|---------|--------------|------------|--------|
| - | - | - | - | - | - | - |

---

## Notes

- R model uses global variables extensively - document each dependency when porting
- Pay attention to vectorization differences between R and Python (numpy/pandas)
- Watch for 1-based (R) vs 0-based (Python) indexing issues
- Document any assumptions made when R code is ambiguous
- Use small test cases first (single year, single membership class) before full runs
- Consider using pytest's parametrize for testing multiple scenarios efficiently
