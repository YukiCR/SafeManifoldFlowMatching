# 03 — Reproduce complete motion by autonomous replanning

**What to build:** The applicant can run the 35 seeded autonomous rollouts using generated history, evaluate geometry and motion quality, and see the declared freeze-gate outcome.

**Blocked by:** 02 — Learn and sample real LShape conditional chunks. Satisfied.

**Status:** ready-for-agent
**Progress:** completed

- [x] Eight predicted/four used indexing and final partial execution are correct.
- [x] Future demonstration states never enter generated-history conditioning.
- [x] DTW, goal error, jumps, validity, runtime and all failure labels are reported.
- [x] The declared gate is evaluated without silently changing thresholds.

## Comments

Applicant approved this ticket and its test interfaces. See the parent specification and ticket plan.

Completed on 29 October 2026. The all-context 200-epoch run passed 35/35 autonomous rollouts with unchanged thresholds. Dataset, checkpoint, split/draw records, figures, failure history and numerical/reload checks are preserved. See [Phase 1 report](../../../docs/results/phase1_report.md). Phase 2 is not implemented.
