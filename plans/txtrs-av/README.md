# TXTRS-AV Runtime Scaffold

This folder is the runtime target for the fresh AV-first `txtrs-av` onboarding.

Current state:

- first-cut `config/plan_config.json` committed
- first-cut AV-built demographics and reduction tables committed
- first-cut AV-built retirement and termination tables committed
- first-cut AV-built `funding/init_funding.csv` committed
- first-cut AV-built `demographics/retiree_distribution.csv` committed
  (life annuities only; disabled and survivors deferred — see issue #71)
- mortality files and `funding/return_scenarios.csv` still pending
- prep work should build source-supported artifacts here in later passes

Rules:

- do not copy existing `plans/txtrs/**` artifacts here silently
- only add config or data files once their provenance and scope are explicit

Current config stance:

- AV-first
- DB-only
- explicit about provisional runtime approximations, especially the
  vested-by-2014 cohort encoding and mortality placeholders
