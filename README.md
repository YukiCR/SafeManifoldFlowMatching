# SafeManifoldFlowMatching

**Final direct-S² audit passed. Phase 1 specification, four tickets, local workflow and the two test interfaces are approved. Ticket 01 is complete; ticket 02 is blocked by the missing official LShape MAT file.** Start with the consolidated [core methodology](methodology.md). The applicant requires grilling → approved proposal → specification → approved tickets → TDD. Maximum project time is 18 hours, with headroom for the 30 October application.

The previous chain results and obsolete agent-created implementation were deleted on 29 October 2026. Phase 1 sphere geometry and analytical test fixtures are implemented. Six tests pass. No real LASA preparation, model training, learned checkpoint, motion-reproduction benchmark or Phase 2 implementation has occurred.

Approved design choices so far:

- A robotic pointing direction on **S²**; full attitude and torque dynamics are outside the current proposal.
- CBF correction of the **FM generation process**. Filtering a downstream trajectory follower is a fallback only if the preferred design cannot fit the time budget.
- **Phase 1 reimplements original RFMP's LASA method**, inheriting its documented decisions: short position chunks on a product of spheres, observation-history conditioning and receding-horizon rollout. This supersedes the earlier complete-trajectory formulation for Phase 1.
- **Connecting arcs may be unsafe.** Waypoint safety is not a continuous-motion guarantee.
- **Dynamic-consistency guarantees are out of scope.**
- **Unconstrained initial noise with terminal waypoint-safety recovery**, following SAD-Flower. Intermediate generated candidates may be unsafe.
- **Two development phases:** first reproduce RFMP without safety; then steer those same RFMP position chunks inside FM generation, retaining the replanning loop and frozen Phase 1 model. The applicant approved this Phase 2 structure. Preserve a reproducible Phase 1 baseline before Phase 2.
- **Initial dataset:** one LASA handwriting family, **LShape**, embedded on S².
- **Version control:** a dedicated local Git repository named SafeManifoldFlowMatching.

The Phase 1 method, documented RFMP settings and Phase 2 chunk/replanning structure are selected. Do not add hard start/goal pinning, a new sequence architecture or mandatory SRFMP to that reproduction. The applicant approved the [proposal](proposal.md), requested consolidated/standalone review, and now conditionally authorizes progressing to Phase 1 after the final direct-S² audit. Undocumented reproduction details and numerical/evaluation settings remain unresolved and must not be silently invented.

Phase 1's method design is settled; its remaining reproduction details will be explicit in the specification. The [Phase 2 methodology draft](methodology_phase2.md) records the approved chunk/replanning structure and internal angular safety margin: filter against a slightly expanded forbidden cone, evaluate against the actual cone. The margin magnitude, numerical settings and measurable evaluation thresholds remain specification items.

The applicant selected **stop on an unsafe next execution portion**: reject that portion before advancing, retain the last accepted direction and count a rollout failure. No fresh-noise retries. The filter still constrains the complete prediction horizon; unused-tail violations are reported separately. The three [standalone reviews are complete](docs/reviews/README.md), with factual clarifications and numerical risks recorded. The [final direct-S² audit](docs/reviews/final_s2_audit.md) passed. The [Phase 1 specification](.scratch/rfmp-phase1/spec.md) and [ticket/test-interface plan](.scratch/rfmp-phase1/ticket_plan.md) are approved. Progress and red–green evidence are in the [TDD log](docs/phase1_tdd_log.md).

The follow-up [manifold implementation audit](docs/reviews/manifold_implementation_audit.md) reads the geometric-CBF controller/dynamics source and official RFM geometry code. The method now explicitly states its product manifold, tangent bundle, round metric, intrinsic training/filter interpretation and geometric diagnostics. The satellite reference is a mechanical SO(3) system; our approved scope remains a first-order generator on a product of S² factors.

The final applicant decision is **geometry throughout, directly on S²**. This overrides the former SO(3) lift/body-coordinate selection. The selected filter minimizes the round-metric change from RFMP's tangent velocity under the intrinsic barrier inequality; integrate using the sphere exponential. No frame, roll or Lie-algebra variables are needed. Earlier SO(3) reports remain historical evidence only.

The [data-source comparison](data_options.md) records the alternatives and the selection of LASA LShape. Its small number of independent demonstrations limits the conclusions of the initial trial.

The Git root is `application/SafeManifoldFlowMatching/`; `application/project/` remains a compatibility symlink. Raw/processed datasets, checkpoints and run artifacts are ignored by default. The current repository contains planning documents only. The GitHub remote is https://github.com/YukiCR/SafeManifoldFlowMatching.git. Local setup and remote publication status are verified separately.

Research notes:

- [Flow matching and stable policy paper](docs/references/flow_matching_and_stability.md).
- [SAD-Flower and geometric CBF paper](docs/references/manifold_safety_references.md).
- [LASA FM/diffusion implementation decisions and evidence limits](docs/references/lasa_implementation_comparison.md).

The research notes distinguish paper results, source availability and our proposed adaptations. They are not evidence of completed applicant project experience.

Phase 1 environment checks found a working existing scientific Python environment with CPU execution and torch.func.jvp; CUDA is unavailable. No real LShape MAT file was found locally and shell download failed. This blocks real-data learning, not the first approved geometry ticket. Ticket 01 is implemented and tested; real-data learning remains blocked.

## Phase 1 development

The approved interfaces are sphere geometry and the Phase 1 study. Current implementation covers sphere exp/log, geodesic/JVP targets and factorwise exponential-Euler integration with explicit invalid-point/tangent/cut-locus errors.

Run the current tests from this repository:

```bash
/home/chengrui/miniconda3/envs/latentSafety/bin/python -m pytest -q
```

Place the official LShape MAT file at `data/raw/LShape.mat` to unblock the real-data ticket. Raw records and generated artifacts are ignored by Git. Geometry test success is not evidence of successful motion learning.
