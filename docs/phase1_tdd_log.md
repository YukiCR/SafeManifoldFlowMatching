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
