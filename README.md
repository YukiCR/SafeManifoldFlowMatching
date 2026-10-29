# SafeManifoldFlowMatching

**No project implementation is approved.** The applicant requires grilling → approved proposal → specification → approved tickets → TDD. Maximum project time is 18 hours, with headroom for the 30 October application.

The previous chain results and obsolete agent-created implementation were deleted on 29 October 2026. No new project code, tests, demonstrations, training or experiments have been created or run.

Approved design choices so far:

- A robotic pointing direction on **S²**; full attitude and torque dynamics are outside the current proposal.
- CBF correction of the **FM generation process**. Filtering a downstream trajectory follower is a fallback only if the preferred design cannot fit the time budget.
- **Phase 1 reimplements original RFMP's LASA method**, inheriting its documented decisions: short position chunks on a product of spheres, observation-history conditioning and receding-horizon rollout. This supersedes the earlier complete-trajectory formulation for Phase 1.
- **Connecting arcs may be unsafe.** Waypoint safety is not a continuous-motion guarantee.
- **Dynamic-consistency guarantees are out of scope.**
- **Unconstrained initial noise with terminal waypoint-safety recovery**, following SAD-Flower. Intermediate generated candidates may be unsafe.
- **Two development phases:** first reproduce RFMP without safety; then safety steering inside the FM sampler. Preserve a reproducible Phase 1 baseline before Phase 2. Whether Phase 2 steers those same chunks or uses a separate complete-trajectory formulation awaits the applicant's answer.
- **Initial dataset:** one LASA handwriting family, **LShape**, embedded on S².
- **Version control:** a dedicated local Git repository named SafeManifoldFlowMatching.

The Phase 1 method and documented RFMP settings are selected. Do not add hard start/goal pinning, a new sequence architecture or mandatory SRFMP to that reproduction. Undocumented preprocessing/split details and Phase 2 scope remain to be resolved. Overall proposal approval and the specification/tickets/TDD stages remain pending. See the [provisional proposal](proposal.md).

The [data-source comparison](data_options.md) records the alternatives and the selection of LASA LShape. Its small number of independent demonstrations limits the conclusions of the initial trial.

The Git root is `application/SafeManifoldFlowMatching/`; `application/project/` remains a compatibility symlink. Raw/processed datasets, checkpoints and run artifacts are ignored by default. The current repository contains planning documents only. The GitHub remote is https://github.com/YukiCR/SafeManifoldFlowMatching.git. Local setup and remote publication status are verified separately.

Research notes:

- [Flow matching and stable policy paper](docs/references/flow_matching_and_stability.md).
- [SAD-Flower and geometric CBF paper](docs/references/manifold_safety_references.md).
- [LASA FM/diffusion implementation decisions and evidence limits](docs/references/lasa_implementation_comparison.md).

The research notes distinguish paper results, source availability and our proposed adaptations. They are not evidence of completed applicant project experience.
