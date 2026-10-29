# 04 — Freeze and explain the baseline

**What to build:** The applicant receives a reproducible baseline manifest, plots and a concise report, or an honest preserved failure report if validation fails.

**Blocked by:** 03 — Reproduce complete motion by autonomous replanning. Satisfied.

**Status:** ready-for-agent
**Progress:** completed

- [x] Source/checkpoint/configuration/split hashes and baseline Git reference are preserved.
- [x] Reproduction commands and geometric visualizations are available.
- [x] Passed, failed and blocked work is distinguished in the report.
- [x] Phase 2 remains blocked without a validated frozen Phase 1 baseline.

## Comments

Applicant approved this ticket and its test interfaces. See the parent specification and ticket plan.

Completed on 29 October 2026. The all-context 200-epoch run passed 35/35 autonomous rollouts with unchanged thresholds. Dataset, checkpoint, split/draw records, figures, failure history and numerical/reload checks are preserved. See [Phase 1 report](../../../docs/results/phase1_report.md). Phase 2 is not implemented.
