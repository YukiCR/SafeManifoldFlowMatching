# SafeManifoldFlowMatching working rules

This is a small research-preparation project for Chengrui Shi's KTH application. Read `README.md` and `proposal.md` before working. Parent workspace instructions also apply.

- Project implementation is not yet approved. Follow grilling → approved proposal → specification → approved vertical-slice tickets → TDD at agreed public boundaries.
- Ask design questions one at a time and record decisions. A recommendation is not approval.
- Initial data source is **LASA LShape only**, mapped onto S². Preserve source provenance and data-use terms; split by original demonstration before augmentation.
- One FM sample is a whole pointing trajectory on a product of spheres. CBFs act inside generation, with unconstrained source noise and terminal waypoint recovery, referring to SAD-Flower and geometric CBFs.
- Phase 1: manifold FM only. Phase 2: safety steering. Preserve a validated Phase 1 model/configuration and baseline commit before Phase 2. Do not mix safety changes into Phase 1.
- Connecting arcs may be unsafe; waypoint safety is not a continuous-path guarantee. Dynamic-consistency guarantees are out of scope.
- Total project budget is at most 18 hours, preserving application preparation headroom before 30 October. Do not silently expand scope.
- Keep coherent Git commits, with model/data configuration and provenance tracked. External datasets, model checkpoints and generated run artifacts are ignored by default. No remote/push or publication is authorized by local Git setup.
- Do not include private application records, shared CVs, credentials or certificates in this repository. Do not claim proposed/unperformed work or unreviewed agent artifacts as applicant achievements.
