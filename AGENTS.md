# SafeManifoldFlowMatching working rules

This is a small research-preparation project for Chengrui Shi's KTH application. Read `README.md` and `proposal.md` before working. Parent workspace instructions also apply.

- Project implementation is not yet approved. Follow grilling → approved proposal → specification → approved vertical-slice tickets → TDD at agreed public boundaries.
- Ask design questions one at a time and record decisions. A recommendation is not approval.
- Initial data source is **LASA LShape only**, mapped onto S². Preserve source provenance and data-use terms. RFMP reports an 80/10/10 split but its split unit is unverified; resolve and document this in the spec. Overlapping windows are not independent recordings, and a window split must not be described as held-out-demonstration generalization.
- User decided Phase 1 reimplements original RFMP's LASA method and inherits its documented decisions. Generate short position chunks on a product of spheres, condition on observation history, and roll out with replanning. No hard start/goal pinning. This supersedes the earlier complete-trajectory proposal for Phase 1. Do not silently invent undocumented paper details.
- Phase 1: reproduce ordinary RFMP without safety. Phase 2: generation-time safety steering, with unconstrained source noise and terminal waypoint recovery referring to SAD-Flower/geometric CBFs. Whether Phase 2 uses the same RFMP chunks or a separate complete-trajectory model is pending; do not decide on the user's behalf. Preserve the validated Phase 1 model/configuration and baseline commit; do not mix safety changes into Phase 1.
- Connecting arcs may be unsafe; waypoint safety is not a continuous-path guarantee. Dynamic-consistency guarantees are out of scope.
- Total project budget is at most 18 hours, preserving application preparation headroom before 30 October. Do not silently expand scope.
- Keep coherent Git commits, with model/data configuration and provenance tracked. External datasets, model checkpoints and generated run artifacts are ignored by default. No remote/push or publication is authorized by local Git setup.
- Do not include private application records, shared CVs, credentials or certificates in this repository. Do not claim proposed/unperformed work or unreviewed agent artifacts as applicant achievements.
