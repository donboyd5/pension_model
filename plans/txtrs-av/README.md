# TXTRS-AV Runtime Scaffold

This folder is the runtime target for the fresh AV-first `txtrs-av` onboarding.

Current state:

- first-cut `config/plan_config.json` committed
- first-cut AV-built demographics and reduction tables committed
- retiree distribution, retirement/termination tables, mortality files, and
  funding files still pending
- prep work should build source-supported artifacts here in later passes

Rules:

- do not copy existing `plans/txtrs/**` artifacts here silently
- only add config or data files once their provenance and scope are explicit

Current config stance:

- AV-first
- DB-only
- explicit about provisional runtime approximations, especially the
  vested-by-2014 cohort encoding and mortality placeholders
