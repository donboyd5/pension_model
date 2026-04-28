# TXTRS-AV Runtime Scaffold

This folder is the runtime target for the fresh AV-first `txtrs-av` onboarding.

Current state:

- first-cut `config/plan_config.json` committed
- first-cut AV-built demographics and reduction tables committed
- first-cut AV-built retirement and termination tables committed
- first-cut AV-built `funding/init_funding.csv` committed
- first-cut AV-built `demographics/retiree_distribution.csv` committed
  (life annuities only; disabled and survivors deferred — see issue #71)
- first-cut AV-built `mortality/base_rates.csv` and
  `mortality/improvement_scale.csv` committed. Active half is source-direct
  from SOA Pub-2010(B) Teacher Below-Median Income; retiree half is the
  documented fallback estimator since the AV-named 2021 TRS healthy-retiree
  table is not public. See `prep/txtrs-av/reports/first_cut_av_data_batch_05_mortality.md`.
- first-cut `funding/return_scenarios.csv` committed. Modeling-choice
  artifact; runtime overrides `model`/`assumption` columns; recession
  scenarios mirror the legacy txtrs shape. See
  `prep/txtrs-av/reports/first_cut_av_data_batch_06_return_scenarios.md`.
- end-to-end pipeline runs (`pension-model run txtrs-av --no-test`)
- `config/calibration.json` produced by `pension-model calibrate txtrs-av`.
  After calibration: total AAL matches AV exactly (was -6.52% before),
  funded ratio matches AV 77.8%, and the 2054 projection reaches 98.1%
  funded consistent with the AV's 28-year amortization period. The
  per-bucket gaps remain (`pvfb_term_current` absorbs them as a single
  plug — see issue #48). See
  `prep/txtrs-av/reports/av_comparison_year0.md` for the pre/post
  decomposition.
- prep work should build source-supported artifacts here in later passes

Rules:

- do not copy existing `plans/txtrs/**` artifacts here silently
- only add config or data files once their provenance and scope are explicit

Current config stance:

- AV-first
- DB-only
- explicit about provisional runtime approximations, especially the
  vested-by-2014 cohort encoding and mortality placeholders
