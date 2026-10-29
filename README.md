# SafeManifoldFlowMatching

**Proposal approved; specification and tickets explicitly on hold for methodology review. No project implementation is approved.** Start with the consolidated [core methodology](methodology.md). The applicant requires grilling → approved proposal → specification → approved tickets → TDD. Maximum project time is 18 hours, with headroom for the 30 October application.

The previous chain results and obsolete agent-created implementation were deleted on 29 October 2026. No new project code, tests, demonstrations, training or experiments have been created or run.

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

The Phase 1 method, documented RFMP settings and Phase 2 chunk/replanning structure are selected. Do not add hard start/goal pinning, a new sequence architecture or mandatory SRFMP to that reproduction. The applicant approved the [proposal](proposal.md), then explicitly requested a consolidated method and standalone reviews before any specification or tickets. Undocumented reproduction details and numerical/evaluation settings remain unresolved and must not be silently invented.

Phase 1's method design is settled; its remaining reproduction details will be explicit in the specification. The [Phase 2 methodology draft](methodology_phase2.md) records the approved chunk/replanning structure and internal angular safety margin: filter against a slightly expanded forbidden cone, evaluate against the actual cone. The margin magnitude, numerical settings and measurable evaluation thresholds remain specification items.

The applicant selected **stop on an unsafe next execution portion**: reject that portion before advancing, retain the last accepted direction and count a rollout failure. No fresh-noise retries. The filter still constrains the complete prediction horizon; unused-tail violations are reported separately. Standalone mathematical, RFMP-fidelity and practical reviews are in progress. Applicant review of [methodology.md](methodology.md) precedes any specification or tickets.

The [data-source comparison](data_options.md) records the alternatives and the selection of LASA LShape. Its small number of independent demonstrations limits the conclusions of the initial trial.

The Git root is `application/SafeManifoldFlowMatching/`; `application/project/` remains a compatibility symlink. Raw/processed datasets, checkpoints and run artifacts are ignored by default. The current repository contains planning documents only. The GitHub remote is https://github.com/YukiCR/SafeManifoldFlowMatching.git. Local setup and remote publication status are verified separately.

Research notes:

- [Flow matching and stable policy paper](docs/references/flow_matching_and_stability.md).
- [SAD-Flower and geometric CBF paper](docs/references/manifold_safety_references.md).
- [LASA FM/diffusion implementation decisions and evidence limits](docs/references/lasa_implementation_comparison.md).

The research notes distinguish paper results, source availability and our proposed adaptations. They are not evidence of completed applicant project experience.
