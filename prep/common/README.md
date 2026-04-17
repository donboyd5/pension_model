# Common Prep Area

`prep/common/` holds upstream prep assets that are shared across plans.

Use this area for:

- shared source registries and schemas
- common external reference documents, such as SOA mortality tables
- reviewed shared reference tables derived from those sources
- shared validation checks
- shared estimation methods
- shared source-faithful transform methods
- shared legacy-reconstruction method notes when they reveal reusable patterns
- shared build/export utilities
- shared cross-plan lessons and prep design memos

Recommended usage:

- raw shared source documents: `sources/`
- reviewed shared tables derived from those sources: `reference_tables/`
- shared schema and registry specs: `schemas/`
- shared validation logic and check specs: `checks/`
- shared estimation methods: `methods/`
- shared build/export logic or specs: `build/`
- shared reports: `reports/`

This area is upstream prep only. Runtime inputs still belong under `plans/{plan}/`.

Key shared knowledge artifacts:

- [methods/method_registry.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/methods/method_registry.md)
- [reports/cross_plan_lessons.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/reports/cross_plan_lessons.md)
- [reports/first_year_cashflow_review_template.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/reports/first_year_cashflow_review_template.md)
- [reports/mortality_basis_review_template.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/reports/mortality_basis_review_template.md)
- [reports/new_plan_readiness_checklist.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/reports/new_plan_readiness_checklist.md)
