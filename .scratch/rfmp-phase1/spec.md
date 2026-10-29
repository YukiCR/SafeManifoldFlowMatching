# Phase 1 specification — original RFMP on spherical LShape

**Status: ready-for-agent — applicant approved the specification/tickets/test interfaces and subsequently approved all-context epoch expansion on 29 October 2026.** Final direct-S² methodology passed its independent audit. This specification fixes previously undocumented reproduction choices openly; it does not claim these choices were verified in author code. Phase 2 is excluded.

## Problem Statement

The applicant needs a small, reproducible RFMP baseline that genuinely learns ordered manifold-valued motion and works under autonomous replanning. Valid sphere outputs or a decreasing training loss alone are insufficient evidence. The baseline must be understandable and frozen before any safety extension, within the remaining project budget.

## Solution

Prepare the seven official LASA LShape recordings, embed their positions on the unit sphere, train the original observation-conditioned position-chunk RFMP, generate motions by repeated prediction and partial execution, and preserve a measured baseline with honest provenance and failure accounting.

Two public test interfaces are proposed: **sphere geometry** for independently checkable manifold operations/training paths, and the **Phase 1 study** for preparation, fitting, generation, rollout and evaluation. Helpers and neural-layer internals are not separate test interfaces.

## User Stories

1. As the applicant, I want the real LShape recordings identified and hashed, so that I can trace results to their source.
2. As the applicant, I want preprocessing fitted only from declared training information, so that evaluation assumptions are explicit.
3. As the applicant, I want ordered spherical positions, so that the learned task retains handwriting geometry.
4. As the applicant, I want context and future positions paired correctly, so that RFMP learns a conditional motion rather than unrelated points.
5. As the applicant, I want exact horizon and padding conventions, so that replanning cannot silently skip or duplicate commands.
6. As the applicant, I want the reported wrapped-Gaussian repeated-point prior, so that the baseline preserves the selected paper method.
7. As the applicant, I want geodesic training paths and tangent targets, so that learning uses the sphere geometry.
8. As the applicant, I want a tangent neural field, so that generated updates remain geometrically meaningful.
9. As the applicant, I want reproducible training and validation, so that checkpoint selection does not depend on fresh validation noise.
10. As the applicant, I want complete replanned rollouts, so that teacher-conditioned predictions cannot conceal drift.
11. As the applicant, I want geometry, shape, goal and jump diagnostics together, so that a trivial or unstable result fails validation.
12. As the applicant, I want explicit numerical and data failures, so that incomplete results are not presented as success.
13. As the applicant, I want a frozen baseline manifest, so that the later safety comparison changes only the intended mechanism.
14. As the applicant, I want concise figures and an explanation of deviations, so that I can discuss the actual work in an interview.
15. As the applicant, I want a bounded CPU-compatible workflow, so that this project leaves time for the application.

## Implementation Decisions

### Inherited choices

- LShape only, seven recordings, 200 ordered positions per recording; position-valued actions on a product of unit round spheres.
- Original RFMP conditioning: reference position, an earlier position from the same available history, and their index separation. Context is fixed during one generation solve.
- Prediction horizon 8 and execution horizon half, with the explicit array interpretation below.
- Wrapped Gaussian at the north pole with reported parameter 0.5, one sampled point repeated across the chunk.
- Geodesic conditional flow matching; MLP with reported depth five/width 64 and learned-parameter Swish; Adam learning rate 0.0001; EMA decay 0.999; 200 epochs; best validation checkpoint.
- Reported split proportions 80/10/10. No hard goal/start pinning, explicit goal input, safety guidance or replacement analytic policy.

### Explicit resolutions of paper gaps

These are **our reproducibility conventions**, not verified original-author implementation facts.

| Gap | Selected convention for this draft |
| --- | --- |
| Horizons | Eight future positions are predicted, four are used. Reference position itself is not one of those eight. This resolves the paper's inclusive-index contradiction by following its prose. |
| Target indexing | With zero-based current reference r, target indices are r+1 through r+8. Clamp training indices beyond 199 to 199, repeating the terminal position. References are 1 through 198. |
| Bootstrap | Supply the first two recorded directions as history. Generation begins after the second. Later conditioning uses generated history, never future demonstrated states. |
| Context | Sample a context index strictly before the reference, from the same recording during training or generated history during rollout. Encode the paper's target-index minus context-index gap divided by 200; this is an explicitly normalized representation of the same index information. |
| Split unit | Partition unique recording/reference pairs before sampling contexts, with seed 0 and floor allocations 80%, 10%, remainder. All context variants of a pair stay together. Record overlapping positions across partitions. This is within-recording reconstruction, not held-out-recording generalization. |
| Resampling | Linear interpolation of positions to 200 normalized-time samples including both endpoints. Use provided time samples if present and valid. Do not reuse original velocity/acceleration labels as sphere vectors. |
| Embedding | Use the dataset's nominal planar goal at the origin and a fixed tangent basis at the north pole. Apply the sphere exponential to scaled planar coordinates. Scale the maximum radius available in training references/history/targets to 60 degrees. Freeze the scale, with no evaluation clipping. Reject invalid/cut-locus inputs explicitly. |
| Gaussian convention | Interpret the reported Gaussian matrix 0.5 times identity as tangent covariance; tangent standard deviation is therefore its square root. This interpretation must be named in every baseline configuration. |
| Network depth | Five hidden affine layers of width 64, one learned scalar Swish parameter per hidden layer, followed by an ambient three-vectors-per-waypoint output projected factorwise to the current tangent spaces. Report actual parameter count; do not claim the paper's approximate count was matched. |
| Network inputs | Current noisy chunk, generation time, reference/context directions and normalized history gap. No rotation frames or safety information. |
| Loss | Batch mean of the product-metric squared tangent errors, summing over sphere factors. Target derivative obtained by differentiating the source-to-data geodesic with respect to generation time. Both compared vectors are based at the intermediate chunk. |
| Training | Batch size 128, seed 0, one pass over ALL valid training window/context pairs per epoch, with the window split fixed before expansion; reshuffle expanded pairs and resample source noise/time. The applicant approved this correction after the first window-only run failed. Adam defaults other than the reported learning rate. No weight decay or architecture search. |
| Checkpoint selection | Update EMA after each optimizer step. Evaluate EMA using an immutable validation context/noise/time bank; preserve the best EMA checkpoint and its epoch/score, together with the untrained reference score. Test-bank draws are separate and frozen. |
| Geometry and integration | Sphere exponential Euler, 100 equal generation steps from 0 to 1; evaluate the field at left endpoints. No arbitrary output clipping or Euclidean interpolation. Reject nonfinite values, invalid points or unresolved antipodal logarithms. Coincident exp/log limits are handled. |
| Precision | Float64 for independent geometry checks and geodesic-target construction; float32 model training/sampling. Record actual runtime precision and geometry errors. |
| Rollout ending | Retain a total of 200 positions including the two supplied bootstrap positions. On the final replan use only the remaining required portion. Horizon completion and goal-reaching success are separate. |

The sphere geometry module has a small mathematical interface for tangent projection, metric/distance, exp/log and a differentiable source-to-data path with its tangent target. The Phase 1 study module owns data provenance, conditioning, model/training, sampling, rollout and baseline reporting behind its public study interface. Do not introduce a general-purpose manifold framework or mockable layers for hypothetical future implementations.

### Evaluation and Phase 1 freeze gate

- Fixed evaluation suite: each of the seven recorded bootstrap pairs, with five source-noise seeds, giving 35 attempted rollouts. These are not 35 independent human demonstrations. Preserve exact draws or index-based draw schedules.
- Report window-level test flow loss, angular dynamic-time-warping shape error against the corresponding recording, terminal angular goal error, largest adjacent angular jump, finite/unit-norm/tangent errors and runtime. DTW uses spherical geodesic distance and reports mean cost along its selected alignment path.
- Proposed operational freeze gate: every attempted rollout is finite and manifold-valid; at least 80% jointly achieve final goal error at most 5 degrees, mean angular DTW cost at most 10 degrees, and largest adjacent angular jump at most 20 degrees. Sampling unit-norm residual must be at most 0.00002. Validation loss must improve over the untrained reference; failure to improve is not hidden by selecting a different scoring bank.
- These are applicant-project acceptance thresholds, not reported RFMP results or guarantees. Do not silently loosen them after seeing outcomes. If the gate fails, preserve the failure and diagnose within the time cap; do not begin Phase 2 with a failed baseline or substitute an analytic controller.
- A short bounded training smoke check verifies that optimization can improve a fixed tiny deterministic fixture. Only the real-data 200-epoch study and autonomous rollout suite establish the project baseline; test fixtures are not project demonstration data or performance evidence.
- Freeze the model, exact split and preprocessing, source/checkpoint hashes, model and solver settings, initial histories, draws, evaluation outputs and baseline Git commit. Preserve failed runs and deviation notes.

### Environment and external data

Use the existing Python 3.12 scientific environment with working PyTorch 2.9.1, torch.func.jvp, NumPy, SciPy, Matplotlib and pytest. Runtime checks found CPU execution available and CUDA unavailable. Start with two CPU threads and batch evaluation; record real runtime rather than promising GPU performance. Write caches/artifacts only to the workspace or temporary directory, with a headless plotting backend. Do not mutate the shared environment or recreate the old Meta dependency stack.

The official [LASA repository](https://github.com/epfl-lasa/LASAHandwritingDataset) provides LShape and defines the nominal target at the origin. Preserve its academic-use attribution/terms; raw and transformed records remain untracked. The real MAT file is an external prerequisite. No local copy was found, and shell network access failed; never replace it with invented LShape demonstrations. Geometry/sampler development can proceed with analytical test fixtures while real-data access is resolved.

## Testing Decisions

Proposed interfaces requiring applicant confirmation:

1. **Sphere geometry:** independently known great-circle points/velocities, source-to-target orientation, metric distance, tangency, coincidence and explicit cut-locus failure. Float64 tolerance 0.00000001. Use hand-worked axes/quarter-circle cases, not expected values recomputed with the implementation.
2. **Phase 1 study:** preparation/conditioning/provenance, bounded fit/generate behavior, seeded sphere sampling, generated-history replanning, end-of-rollout behavior and checkpoint/report reproduction through its public study interface. Use actual small stored fixtures; no mocks of internal model layers or helper call counts.

Tests are written one vertical slice at a time: one failing behavior, minimal implementation, then the next behavior. No bulk test-first scaffolding or implementation-first backfill. No existing project tests supply prior art. Expensive scientific validation is a measured run, not a brittle unit test that demands success from an arbitrary training seed. Phase 2 tests are excluded.

## Out of Scope

Phase 2 CBF implementation or tuning; SO(3) lift/frames/roll; image encoders; extra LASA families; synthetic replacement demonstrations; SRFMP; diffusion comparison; broad hyperparameter sweeps; physical hardware, dynamics consistency, arc-safety enforcement or global convergence guarantees; public dataset/checkpoint redistribution.

## Further Notes

The final method audit found no methodology blockers. The specification choices above resolve operational gaps openly and remain reviewable. Source: [original RFMP](https://arxiv.org/html/2403.10672v1); [final method audit](../../docs/reviews/final_s2_audit.md).

The project hard stop remains 30 October 09:45 China time or earlier at the 18-hour total cap. Approximately seven hours of the conservative preparation/discussion window had elapsed at 22:45 on 29 October. Reserve at most five additional hours for Phase 1, including its workflow gates and baseline preparation; work stops sooner if the overall deadline or budget is reached. A partial, failed or blocked Phase 1 remains honestly reportable and does not authorize Phase 2.

## Approved epoch correction and requested visualization

The first run used 1,108 windows per epoch (1,800 updates across 200 epochs) and failed 0/35 rollouts. It is preserved under runs/phase1-baseline. The applicant approved expanding the fixed training windows to all 109,739 valid context pairs: 858 batches per epoch and 171,600 updates in 200 epochs. Keep model/prior/learning rate/EMA/validation bank/gate thresholds unchanged. Bounded unit fixtures may retain window mode explicitly; scientific training defaults to all-context mode.

The applicant requested a paper-style six-panel spherical transport visualization. Use actual same-sample snapshots at generation times 0, 0.5 and 1, orange embedded demonstrations and blue first predicted positions from joint generated chunks. Rows are validation-window and test-window conditions, clearly labeled rather than claiming a stable-model comparison. Preserve plotted sample banks and export PNG/PDF; separately report autonomous rollout quality.

## Execution outcome

Completed 29 October 2026: the approved all-context 200-epoch study passed 35/35 autonomous rollouts without threshold changes. See the [baseline report](../../docs/results/phase1_report.md). Earlier data-access notes describe the resolved planning-stage blocker. All four Phase 1 tickets are complete. No Phase 2 implementation is included.
