# Phase 1 red–green evidence

The applicant approved the Phase 1 specification, four tickets and two public test interfaces before any project test was written. Analytical fixtures below are unit-test inputs, not synthetic replacement demonstration data or project learning results.

| Cycle | Public behavior | Red observation | Green observation |
| --- | --- | --- | --- |
| 01 | Source-to-data quarter-great-circle point and velocity | Test collection failed: project package absent | One test passed with independent analytical values |
| 02 | Coincident inputs produce a constant path and zero tangent target | Coincident path returned NaNs | Two tests passed, including finite zero target |
| 03 | Antipodal path reports a nonunique logarithm | Expected cut-locus error was not raised | Three tests passed with explicit cut-locus rejection |
| 04 | Integrating a known tangent field produces a valid product-sphere chunk | Public integration operation absent | Four tests passed with analytical endpoint and per-factor norms |
| 05 | Radial fields are rejected rather than treated as tangent motion | No error was raised for a radial field | Five tests passed with finite/unit/tangent validation |
| 06 | Small integration steps cannot hide a radial velocity | A radial field passed after division by the step count | Complete suite: six tests passed |

Ticket 01 completed on the CPU in the existing scientific environment. Final check: `python -m pytest -q` — 6 passed. The test runner emitted an environment-level argparse warning on the whole-suite command; tests passed. No real-data preparation, fitting, checkpoint, rollout benchmark or Phase 2 implementation has occurred.

The exponential computes the spherical formula then removes floating-point norm drift; it is not normalized ambient Euler and not a safety repair. Both point validity and unscaled field tangency are checked before integration. The real LShape file is not present and shell download failed, so ticket 02 remains blocked.

## Real-data learning and evaluation cycles

| Cycle | Public behavior | Red observation | Green observation |
| --- | --- | --- | --- |
| 07 | MAT preparation and declared spherical embedding | Study module absent | Seven recordings resample/embed with known fixture goal/radius |
| 08 | Past context and terminal padding | Batch operation absent; first attempt exposed float32 gap rounding | Correct paired history, gap and padded future targets |
| 09 | Repeated-point wrapped prior and reproducible bank | Noise field absent | Same draw per chunk, unit sphere and seed reproducibility |
| 10 | Bounded fitting and generation | Fit operation absent | Fixed validation bank improves and samples are valid |
| 11 | Safe checkpoint round trip | Loader absent | Identical seeded generated output after reload |
| 12 | Autonomous history and last partial execution | Rollout operation absent | Reference indices 1,5,9 and past-only conditioning verified |
| 13 | Intrinsic angular metric | Distance operation absent | Quarter-circle distance is pi/2 |
| 14 | Actual generation-time snapshots | Snapshot argument absent | Source/middle/returned chunk captured without substitution |
| 15 | Failure-inclusive scientific evaluation | Evaluation operation absent | Known success and antipodal failure retained as 1/2 successes |
| 16 | Full context-expanded epoch | Epoch mode absent | All valid contexts and actual update count verified |

Complete suite after these cycles: 16 tests passed. The first real-data 200-epoch window-only run failed its scientific gate; the applicant approved the epoch correction before retraining. Scientific validation is separate from test-fixture success.

## Completed real-data validation

The applicant supplied the official LShape MAT file, which passed record/time/finite/goal checks. The approved all-context run completed 200 epochs and 171,600 optimizer steps in 572.45 seconds. Best EMA epoch: 192; validation loss 0.038979; test loss 0.084126. All 35 autonomous rollouts passed the unchanged gate. The 16-test suite passed before the full run; no learning/sampling code changed during fitting. The subsequent visualization-only change enlarged panels. Saved-checkpoint generation and all saved rollout scores were verified after fitting.

The six-panel PNG/PDF uses actual generation snapshots; no illustrative image or synthetic demonstration was substituted. The initial window-only failed run remains preserved. See the [final report](results/phase1_report.md) and [manifest](results/phase1_baseline.json). All four Phase 1 tickets are complete; Phase 2 has not begun. Earlier missing-data and six-test statements above are chronological records of the first ticket, not current blockers.
