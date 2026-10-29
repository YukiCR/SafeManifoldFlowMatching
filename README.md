# SafeManifoldFlowMatching

**No project implementation is approved.** The applicant requires grilling → approved proposal → specification → approved tickets → TDD. Maximum project time is 18 hours, with headroom for the 30 October application.

The previous chain results and obsolete agent-created implementation were deleted on 29 October 2026. No new project code, tests, demonstrations, training or experiments have been created or run.

Approved design choices so far:

- A robotic pointing direction on **S²**; full attitude and torque dynamics are outside the current proposal.
- CBF correction of the **FM generation process**. Filtering a downstream trajectory follower is a fallback only if the preferred design cannot fit the time budget.
- Whole-trajectory generation on a **product of spheres**, primarily referencing RFMP, geometric CBFs and SAD-Flower.
- **Connecting arcs may be unsafe.** Waypoint safety is not a continuous-motion guarantee.
- **Dynamic-consistency guarantees are out of scope.**
- **Unconstrained initial noise with terminal waypoint-safety recovery**, following SAD-Flower. Intermediate generated candidates may be unsafe.
- **Two development phases:** first manifold FM alone; then safety steering inside the FM sampler. Preserve a reproducible Phase 1 baseline before Phase 2.
- **Initial dataset:** one LASA handwriting family, **LShape**, embedded on S².
- **Version control:** a dedicated local Git repository named SafeManifoldFlowMatching.

The data-source decision is settled. Endpoint conditioning, model variants and evaluation details remain to be agreed. Overall proposal approval and the specification/tickets/TDD stages remain pending. See the [provisional proposal](proposal.md).

The [data-source comparison](data_options.md) records the alternatives and the selection of LASA LShape. Its small number of independent demonstrations limits the conclusions of the initial trial.

The Git root is `application/SafeManifoldFlowMatching/`; `application/project/` remains a compatibility symlink. Raw/processed datasets, checkpoints and run artifacts are ignored by default. The current repository contains planning documents only. A remote or publication has not been configured.

Research notes:

- [Flow matching and stable policy paper](../research/flow_matching_and_stability.md).
- [SAD-Flower and geometric CBF paper](../research/manifold_safety_references.md).

The research notes distinguish paper results, source availability and our proposed adaptations. They are not evidence of completed applicant project experience.
