# SafeManifoldFlowMatching: core methodology for review

29 October 2026. **Proposal approved; three standalone reviews complete; applicant methodology review pending. Specification and tickets are explicitly on hold.** No project code, tests, dataset preparation, model training or experiments have been performed. This document consolidates the method and factual clarifications from review. See the [review summary and reports](docs/reviews/README.md).

## 1. Purpose and scope

Demonstrate learning, manifold geometry, safety control and robotics through a small **S² robot-pointing** study: can a learned motion generator adapt to a forbidden viewing/tool direction through correction of its generation dynamics?

- Initial data: **LASA LShape only**, human handwriting positions embedded on S²; not recorded robot pointing data.
- **Phase 1:** reimplement the original RFMP LASA method, inheriting its documented choices.
- **Phase 2:** freeze that validated model; add generation-time geometric CBF steering to the same position chunks and retain the replanning loop.
- No physical robot, full SO(3), torque dynamics, learned dynamics model, dynamic-consistency CLF, hard goal pinning or mandatory SRFMP.
- **At most 18 hours including preparation**, with the approved project hard stop of **30 October 2026, 09:45 China time**, or earlier if the budget is exhausted. Preserve application preparation time before the 30 October deadline.

Intended evidence comprises a reproducible nominal baseline, the safety extension, paired evaluation, visualizations and an explanation of derivations, failures and limitations. The time budget is a ceiling, not a promise that both phases will succeed. If Phase 1 does not validate, stop rather than building Phase 2 on an unvalidated model. An incomplete or unsuccessful experiment must remain described as such.

## 2. References and division of roles

| Reference | What we inherit/use | What we do not claim |
| --- | --- | --- |
| Braun, Jaquier, Rozo and Asfour, [RFMP, IROS 2024](https://arxiv.org/html/2403.10672v1) | LASA position-chunk learning, observation/context conditioning and receding-horizon inference | Reproduction of every family, image experiment, diffusion baseline or all reported numerical results |
| Chen and Lipman, [Riemannian FM, ICLR 2024](https://arxiv.org/abs/2302.03660) | Geodesic conditional flow matching, tangent fields, manifold integration | Safety or physical goal-reaching guarantees |
| de Sa, Ong and Ames, [geometric CBFs](https://arxiv.org/abs/2510.20202v1) | Intrinsic barrier gradient and minimum-norm tangent correction | Torque-level backstepping or full mechanical-system safety |
| Huang et al., [SAD-Flower](https://arxiv.org/html/2511.05355v3) | Virtual control inside generation; terminal recovery from unsafe candidate coordinates | Complete reproduction, action admissibility, dynamics consistency or automatic inheritance of its theorem |

The later [RFMP/SRFMP paper](https://arxiv.org/abs/2412.10855v3) supplies context. Its distribution-support stability is distinct from physical convergence to a task goal. Official original-author LASA RFMP training/sampling code has not been verified; the source of inherited settings is the paper. See the [implementation audit](docs/references/lasa_implementation_comparison.md).

## 3. What is generated: two time axes

At physical rollout index `k`, RFMP receives observation/context `o_k` and generates a **short sequence of desired positions**, each on S²:

```text
X_s = (x_1(s), ..., x_m(s)) in (S²)^m,
dX_s/ds = V_theta(s, X_s | o_k),      s in [0,1].
```

`s` is FM generation time, not physical motion time. One integration step adjusts the entire candidate chunk jointly. Keep `o_k` fixed within this generation solve. Intermediate candidates are not executed.

### Manifold, metric and tangent bundle

Use the product of unit spheres with the canonical product round metric:

```text
M = (S²)^m,                         dim(M) = 2m,
T_X M = product_i T_(x_i) S²,
T_(x_i) S² = {v_i in R³ : x_i^T v_i = 0},
g_X(V,W) = sum_i v_i^T w_i.
```

A chunk has `3m` stored coordinates but is a point on a `2m`-dimensional manifold. For fixed time/context, `V_theta` is a tangent vector field (a section of `TM`). The virtual input bundle is also `TM`, with identity control action: `U` and `V_theta(X)` belong to **the same fiber `T_X M`**. This is a first-order, fully actuated virtual generator, not a mechanical state on `TSO(3)` or a physical `(q,v)` system on `TS²`.

Embedded arrays represent these objects. Under this explicitly chosen metric, ambient dot products restricted to tangents are intrinsic inner products, and the pointwise projector `P_x=I-xx^T` computes the round-metric tangent projection. Project each sphere factor individually; normalizing one concatenated chunk does not impose the product geometry. The valid embedded representation does not imply that the learned network is rotation-equivariant or that all tangent spaces can be identified with a single fixed plane.

After sampling, advance through the initial execution portion, update the observed history, generate another chunk and replace the old unused tail. The complete motion is assembled by these repeated predictions. **Retain the chunk structure, not identical numerical predictions.** An action in this LASA abstraction is a desired direction/position; it need not be an angular velocity.

## 4. Phase 1: inherited RFMP baseline

| Item | Paper-reported choice to inherit |
| --- | --- |
| Data | Seven recordings per family; use LShape only; represent each recording with 200 ordered time steps |
| Observation/context | `[o_(τ-1), o_c, τ-c]`, with `c ~ Uniform{1,...,τ-2}`, paired with the same recording/history and prediction index; sample context once per generation solve |
| Horizons | Reported prediction horizon 8; execution horizon half. Inclusive displayed vectors suggest 9/5 positions, while execution prose says the first 4 actions. Exact arrays/indices remain unresolved, not verified as 8/4 lengths |
| Sphere prior | Wrapped Gaussian centered at the north pole, reported parameter σ=0.5 in `σI`; repeat one sampled point over the chunk. Covariance versus standard-deviation convention remains unresolved |
| Training paths | Coordinatewise sphere geodesics between source and demonstrated chunks |
| Network | MLP, reported five layers and 64 hidden units; Swish with learnable parameter |
| Optimization | Adam, learning rate 1e-4; EMA decay 0.999; 200 epochs; best validation model |
| Split | Reported 80/10/10; the split unit is not established by the accessible paper description |
| Sampling | Riemannian Euler; generate a chunk, use its execution portion and replan |
| Endpoints | No added hard start/goal mask or explicit final-goal conditioning |

Each predicted field must be tangent, for example `V_i=P_(x_i) F_i(s,X,o)`. The ambient MLP is a parameterization of the tangent field after projection. Use product exponential/logarithm maps, acting factorwise, for the training path:

```text
X_s = Exp_(X_noise)(s Log_(X_noise)(X_data)),
W_s = dX_s/ds in T_(X_s) M,
L = E[ ||V_theta(s,X_s|o)-W_s||²_(g_(X_s)) ].
```

Both regression vectors live at `X_s`, so their subtraction is well typed and needs no parallel transport. Differentiating the source-to-data geodesic by JVP is a verified reference construction. Do not substitute a vector anchored at `X_noise` or `X_data` without the required map/transport. The loss's normalization remains a reproduction detail.

The exponential Euler form is `X_next=Exp_X(ds*V)` (use `V+U` when steering). Per-factor normalized ambient Euler is a different, retraction-based update. Both must be named accurately; the generic RFM repository has several integration configurations and does not verify which original RFMP implementation was used. The exact update/resolution remains explicit later work. Coincident points and antipodal/cut-locus cases also require handling; neither update certifies discrete barrier satisfaction.

Do not substitute an analytic goal-attraction field for learning, independent noise at every waypoint for the repeated-point prior, or a new sequence architecture for the inherited MLP. Any required deviation must be disclosed rather than presented as an RFMP choice.

### Reproduction gaps, not invented facts

The precise planar normalization/sphere embedding, split unit, horizon arrays, Gaussian parameter convention, MLP input shapes/layer counting, batching/epoch definition, validation/EMA-checkpoint handling, rollout bootstrap/context handling, terminal padding and integration resolution are unresolved. The paper's MLP input prose omits the evolving action state despite its field equations; retain the state-dependent `V(s,X|o)` formulation rather than silently dropping `X`. Later rollout observations/context must come from generated history, not future demonstration positions. These need explicit later choices, supported by sources where available. **No specification values are selected by this document.**

Seven recordings can produce many overlapping chunks/context pairs but remain seven independent human demonstrations. An exact 80/10/10 whole-recording split is impossible with seven recordings. A window split cannot establish held-out-recording generalization; a grouped-recording split would be a disclosed change from the reported percentages. Do not assume augmentation or share transformed raw datasets without checking provenance and terms.

The repeated-point prior is correlated and supported on the product manifold's diagonal; it is not an independent full-dimensional product draw. Generic RFM's uniform-sphere base/log-density machinery does not implement this wrapped-Gaussian RFMP choice. Keep that attribution and do not claim a full-dimensional product likelihood for the repeated-point source.

### Baseline preservation

Validate motion learning and manifold adherence before Phase 2: assess finite, valid chunks **and nominal receding-horizon motion**, with reproduction quality, goal progress and adjacent jumps. Low flow-validation loss or good teacher-conditioned chunks alone do not validate an autonomous rollout. Exact measures/thresholds remain unresolved. Preserve checkpoint, exact preprocessing and split unit/indices, configuration, inference settings, initial observation histories, random states and baseline outputs. Record hashes and a baseline Git commit. Do not retrain or change preprocessing in the core safety comparison.

## 5. Phase 2: generation-time safety steering

Use **one static forbidden spherical cap per rollout**, with unit center `c` and requested half-angle `theta`. The cap is supplied to the safety layer; it is not a new input to or training condition for the frozen network. Initially choose a route-conflicting cap with the supplied start and demonstrated goal outside the expanded internal cap; include a no-conflict comparison. Scenario construction will be explicit before final evaluation.

The controlled generator is

```text
dX_s/ds = V_theta(s, X_s | o_k) + U_s.
```

`U` is a virtual tangent correction to the sampler, not a physical robot velocity or torque. Apply constraints to **all predicted positions**, including the unused tail.

### Actual constraint and approved internal margin

The requested safe set is

```text
h_actual(x) = cos(theta) - c^T x >= 0.
```

The applicant selected a slightly expanded internal cap, `theta_int=theta+delta`, with `0<theta<theta_int<pi`. Use

```text
h_i = cos(theta_int) - c^T x_i,
a_i = grad_S² h_i = -(I-x_i x_i^T)c
```

inside the filter. **Evaluate reported safety and execution acceptance against the actual `theta`.** The margin magnitude is unselected. If an internal residual is bounded below by `-eta`, then `h_actual >= cos(theta)-cos(theta+delta)-eta`. This identity explains the margin but supplies no discrete residual bound by itself.

Intrinsically, define `H_i(X)=h_i(x_i)`. Then `grad_g H_i` has only one nonzero factor, `a_i in T_(x_i) S²`, and

```text
dH_i|_X[V+U] = g_X(grad_g H_i, V+U)
              = a_i^T(V_i+U_i).
```

The displayed projection formula for `a_i` is the round-metric Riemannian gradient, not a metric-independent recipe. A mechanical inertia metric or a different input distribution requires a new gradient/control-adjoint derivation; neither is silently imported from the satellite example.

### Minimum-change tangent filter

At each controlled generation step, minimize `(1/2) ||U||²_(g_X)`, equivalently `(1/2) sum_i ||U_i||²` under the declared metric, subject to

```text
a_i^T (V_i + U_i) >= -phi(s) h_i,
U_i in T_(x_i) S².
```

For one cap and independent unbounded tangent corrections, the solution separates across positions. When `||a_i||²>0`,

```text
U_i = max(0, -(a_i^T V_i + phi(s) h_i)/||a_i||²) a_i.
```

This is our specialization of geometric CBF machinery to RFMP generation, not an assertion that the references implement this exact combination. The nominal field still couples positions through the joint chunk.

### User-proposed SO(3)/SO(2) horizontal-frame representation

**Audited representation for applicant review, not a change to the S² learning task.** The applicant proposed writing each direction as `x_i=R_i e3` and expressing the same first-order CBF in body coordinates. The formulas below are mathematically verified under their stated metric and horizontality assumptions; representation adoption/initialization remains part of this method review. Full attitude/roll learning and physical torque dynamics remain outside scope.

Let `pi(R)=R e3`. Its fiber is `R SO(2)`, with the stabilizer understood as rotations fixing `e3`; thus `SO(3)/SO(2) ≅ S²`. For a chunk, the frame space `(SO(3))^m` is an auxiliary lift of `(S²)^m`. Use the normalized bi-invariant metric

```text
g_R(R hat(u), R hat(v)) = u^T v
                       = (1/2) tr[(R hat(u))^T (R hat(v))].
```

The horizontal input space has `Omega^T e3=0`. With `hat(u)v=u×v`, define

```text
h_i(R_i) = cos(theta_int) - c^T R_i e3,
b_i = -e3 × (R_i^T c),
d h_i|_(R_i)[R_i hat(Omega_i)] = b_i^T Omega_i,
grad h_i(R_i) = R_i hat(b_i).
```

These are a differential/metric gradient on SO(3), with `b_i` the body-coordinate representation of the differential. Lift the existing RFMP tangent prediction horizontally:

```text
Omega_nom,i = R_i^T(x_i × v_nom,i),
R_i hat(Omega_nom,i) e3 = v_nom,i.
```

For `b_i != 0`, the body-coordinate minimum-change filter is

```text
lambda_i = max(0, (-b_i^T Omega_nom,i - phi(s)*h_i)/||b_i||²),
Omega_star,i = Omega_nom,i + lambda_i*b_i,
R_i^+ = R_i exp(ds*hat(Omega_star,i)),
x_i^+ = R_i^+ e3.
```

Both `Omega_nom,i` and `b_i` are horizontal, so the optimizer is horizontal even without adding an explicit horizontal constraint to this particular QP. If `a_i=-(I-x_i x_i^T)c`, then `b_i=R_i^T(x_i×a_i)`, `||b_i||=||a_i||`, and `b_i^T Omega_nom,i=a_i^T v_nom,i`. Projection therefore gives exactly the existing S² correction `v_star,i=v_nom,i+lambda_i*a_i`. Moreover the frozen-vector update obeys `R_i exp(ds*hat(Omega_star,i))e3=Exp_(x_i)(ds*v_star,i)` in exact arithmetic. This is equivalence to **exponential Euler**, not to every possible Riemannian integrator or to the exact time-varying ODE solution.

Important qualifications:

- Call this a **horizontal or zero-axial-spin lift**, not globally zero roll. `Omega^T e3=0` permits geometric holonomy: a closed pointing loop can return with a different frame rotation.
- There is no global smooth choice `R=R(x)` over all S². Choose an initial frame by a documented local/branched rule and carry the frame along each generation solve; do not assume a globally smooth roll convention. Different initial fiber rotations produce the same pointing updates under the equivariant lift/filter. The learned network still sees S² directions/context, not arbitrary frame axes.
- The barrier remains degenerate at `x=±c`; lifting does not cure center infeasibility, near-center ill-conditioning, finite-step recovery error or stalls. Retain the approved margin, actual-cone check and stopping rule.
- The metric normalization is essential to the displayed gradient. A generic inertia-weighted metric changes the gradient/weighted correction and may not preserve this round-sphere equivalence. The satellite's physical backstepping law is not inherited.

Full algebra and independent verification: [quotient-lift audit](docs/reviews/quotient_lift_independent.md). Primary background on horizontal lifts, global sections and holonomy: [Welde and Kumar, Section III-B, Proposition 2 and Remark 2](https://arxiv.org/html/2403.04900v2#S3.SS2). This background does not add a tracking controller to our scope.

### Terminal recovery and its limits

Retain the Phase 1 prior **without excluding unsafe cone samples**. Intermediate candidates may be unsafe. Follow SAD-Flower's nominal initial generation interval and controlled later interval; its reference schedule is `phi(s)=gamma/(1-s)^2`, `gamma>0`. Activation, gain, numerical stopping and integration settings are unresolved.

The intended constraint objective concerns positions at the end of generation. For an unsafe initial barrier, the equality solution `h(s)=h(s_on) exp(-integral(phi))` can stay negative at every `s<1` and only approach zero at the singular endpoint. Do not evaluate that singular gain at `s=1` or claim ideal terminal recovery as an exact finite-step certificate. The internal margin and final check are practical measures, not an automatic numerical theorem.

At the unsafe cap center, `a_i=0` and the recovery inequality can be infeasible. Near that center, at angular distance `r`, correction magnitude can grow approximately as `phi(s)*(1-cos(theta_int))/r` for bounded nominal velocity. Thus near-center ill-conditioning and terminal stiffness are coupled risks even without an exactly degenerate sample. At a zero-gradient safe point, zero correction can be feasible. Handle these branches explicitly; denominator clipping alone does not solve an infeasible constraint. Virtual correction is unbounded in the ideal formulation; there is no actuator-feasibility guarantee. The filter also supplies no tangential detour when the nominal field lacks one, so safe stalls remain possible.

## 6. Approved stopping rule

Before advancing, inspect **every position in the next execution portion** against the actual cone. If any is unsafe:

1. Reject the entire execution portion before advancing.
2. Retain the last accepted direction and stop the rollout.
3. Count a rollout failure; do not execute its safe leading subset, resample fresh noise or repair points after generation.

Continue to constrain the full chunk. An unused-tail violation is a whole-chunk constraint failure and is reported separately; it does not alone trigger the execution stopping rule. Invalid geometry and numerical failure also require explicit failure accounting. A stopped rollout is not a completed safe motion.

## 7. Evaluation and claims

**Matched chunks:** compare nominal and steered generation with identical model, observation/context, source chunk and numerical budget. Record actual/internal clearance, unsafe execution-portion and whole-chunk proposal rates **before acceptance**, roughness/adjacent angular jumps, displacement from nominal, intervention size/residuals, runtime and numerical failures.

**Receding-horizon rollouts:** use identical initial histories/scenarios and random-seed schedules; later observation histories can diverge after steering. Apply the same execution stopping check to both nominal and steered Phase 2 comparisons. Report completion, goal error/reaching, pre-acceptance violations, stops/stalls, geometry errors and runtime, retaining failures in the denominator. Preserve the original Phase 1 reproduction separately. If safety changes the numerical grid or stopping time, include an unsteered comparison using that same protocol.

Interpret these diagnostics geometrically: spherical geodesic distance for goal error, adjacent jumps and paired-position displacement; product metric norm for intervention size; per-factor unit-norm and tangency residuals for geometry checks. If roughness compares velocity vectors based at different points, first bring them to a common tangent space by a stated transport, or state an intrinsic common-base-point construction. Raw ambient velocity subtraction is not an intrinsic acceleration. Distance between positions alone requires no tangent transport. Exact diagnostic formulas remain to be selected later.

Zero unsafe executed points obtained solely by stopping is not evidence that CBF steering improved generation. Distinguish goal-reaching completion from merely exhausting a rollout horizon; retain last-accepted goal error for failures. Do not assess fidelity only on favorable survivors or retain only favorable cone placements. Freeze final scenarios, tuning/evaluation separation and thresholds before the final comparison; the conflicting cap should affect returned waypoints, not only connecting arcs. Goal reaching is measured, not guaranteed by a CLF or a pinned endpoint. Preserve actual source draws or an index-based draw schedule so stopped runs do not shift later pairings.

**Explicit limitations:** safe sampled directions do not ensure safe connecting arcs, including the current-to-next-command connection. There is no continuous-path, tracking, dynamic-consistency, global goal-convergence or torque-feasibility guarantee. LASA embedding and one-family results do not establish deformable-object manipulation or general robotics performance.

## 8. Review questions and next gate

Standalone reviewers should independently assess:

- Is the geometric filter and recovery argument correct, with assumptions and failure cases stated accurately?
- Does the baseline faithfully preserve documented RFMP decisions while exposing reproduction gaps?
- Is the combination useful and numerically practical within the remaining time, or does it need a smaller approved scope?
- Do the acceptance rule and metrics separate sampler improvement from stopping, geometry adherence and goal progress?
- Which issues are actual methodology blockers, and which are ordinary choices for a later specification?

Review reports are advisory findings, not new applicant decisions. **The applicant reviews this method before any specification or tickets proceed.** No code, tests, simulations, dataset preparation, training or experiments are authorized by this document or the reviews. Detailed background: [proposal](proposal.md), [Phase 2 derivation](methodology_phase2.md), [reference notes](docs/references/flow_matching_and_stability.md).

Additional implementation-level audit: [geometric-CBF code and manifold interpretation](docs/reviews/manifold_implementation_audit.md), with an independent [official RFM source audit](docs/reviews/rfm_implementation_geometry.md). These make the existing round/product geometry explicit; they do not add a physical controller, numerical defaults or a new algorithm family.
