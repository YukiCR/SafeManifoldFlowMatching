# 02 — Learn and sample real LShape conditional chunks

**What to build:** The applicant can prepare the real records, fit the declared RFMP and generate valid conditional chunks through the public Phase 1 study interface.

**Blocked by:** 01 — Generate an analytically checkable sphere chunk; official LShape MAT file. Both satisfied.

**Status:** ready-for-agent
**Progress:** completed

- [x] Real source hash, seven records and academic attribution are recorded.
- [x] Embedding, split unit/overlap, paired context, padding and prior match the approved specification.
- [x] A bounded training check exercises real optimization; the real-data study attempts the declared 200 epochs.
- [x] Best EMA checkpoint and fixed validation bank are preserved; missing data is an explicit blocker.

## Comments

Applicant approved this ticket and its test interfaces. See the parent specification and ticket plan.

Earlier status, now resolved: ticket 01 was complete; remaining external blocker: no official LShape MAT file is available locally; shell GitHub download failed. Expected local input: data/raw/LShape.mat. No fabricated replacement data will be used.

Official MAT received and validated: SHA-256 3aa960ed9241d4651c7e21240d63d616d215d889e08ce780fc7a5b1334474ce9. Preparation, fitting, generation and checkpoint tests pass. First window-epoch run is preserved as failed; applicant approved all-context epoch correction before the second run.

Completed on 29 October 2026. The all-context 200-epoch run passed 35/35 autonomous rollouts with unchanged thresholds. Dataset, checkpoint, split/draw records, figures, failure history and numerical/reload checks are preserved. See [Phase 1 report](../../../docs/results/phase1_report.md). Phase 2 is not implemented.
