# 01 — Generate an analytically checkable sphere chunk

**What to build:** The applicant can generate a prescribed great-circle chunk through the public sphere geometry interface, with correct source-to-target tangent targets and explicit unsupported-input failures.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent
**Progress:** completed

- [x] Known great-circle points and velocities match independent analytical values.
- [x] Prescribed tangent-flow integration returns the known target while staying on the product sphere.
- [x] Coincidence and cut-locus/invalid-input behavior are explicit.
- [x] Red-before-green evidence is recorded at the approved sphere geometry interface.

## Comments

Applicant approved this ticket and its test interfaces. See the parent specification and ticket plan.

Completed via six red–green cycles. The complete six-test suite passed; see the Phase 1 TDD log. These are analytical test fixtures, not a learned motion benchmark.
