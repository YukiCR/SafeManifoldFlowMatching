# Proposal: generation-time geometric CBFs for Riemannian motion sequences

29 October 2026. **Proposal approved by the applicant. Specification and tickets are explicitly on hold for standalone-agent and applicant review of [methodology.md](methodology.md). Implementation remains unapproved.**

## Purpose

Develop a compact, explainable project demonstrating **learning, manifold geometry, safety control and robotics** for the PhD application. A robotic camera/sensor/tool axis must produce a sequence of pointing directions on S² toward a target while respecting a forbidden angular cone at its generated waypoints.

Primary references are **RFMP**, **From Bundles to Backstepping**, and **SAD-Flower**. Phase 1 specifically reproduces the LASA method of Braun, Jaquier, Rozo and Asfour, *Riemannian Flow Matching Policy for Robot Motion Learning* (IROS 2024). The later RFMP/SRFMP article supplies context, not a requirement to implement SRFMP. Chen/Lipman's general Riemannian FM supplies foundational geometry and training machinery.

## Agreed decisions and boundaries

- **Phase 1 reimplements RFMP and inherits its documented LASA decisions:** generate short position chunks on a product of spheres and reconstruct motions with a receding-horizon rollout. This user decision supersedes the earlier complete-trajectory formulation for Phase 1. The FM integration trace is still generation, not physical motion.
- CBF correction acts **inside the FM generation process**. Downstream trajectory-following filtering is only a fallback if the preferred design cannot fit the time budget.
- Use S² pointing; full SO(3), visual perception, torque dynamics and hardware deployment are outside the current scope.
- **Connecting arcs can be unsafe.** Generated waypoint safety must not be reported as a guarantee for continuous interpolated motion.
- **No dynamic-consistency guarantee.** Sphere membership and waypoint constraints do not establish physical state/action consistency.
- For Phase 2, start generated position coordinates from **sphere-valued noise unconstrained by the forbidden cone** and recover waypoint safety by the end of generation, referring to SAD-Flower. Intermediate candidates may be unsafe. This does not require uniform noise over the full sphere.
- Maximum project work: **18 hours**, preserving headroom for the 30 October application.
- Develop in two auditable phases: **Phase 1, reproduce RFMP without safety; Phase 2, add safety steering inside generation.** The applicant approved retaining the same RFMP position-chunk horizons, replanning loop and frozen model for Phase 2. Establish a reproducible Phase 1 baseline before beginning Phase 2.
- Initial trials use **LASA LShape only**, mapped onto S². Do not expand to multiple families or switch to synthetic training data without agreement.
- Manage the project with its own Git repository, **SafeManifoldFlowMatching**, at `application/SafeManifoldFlowMatching/`.
- **Failure policy:** before advancing the rollout, inspect the entire next execution portion against the actual cone. If any of its directions is unsafe, reject that portion, stop at the last accepted direction and count a failed rollout. No partial-prefix execution, fresh-noise retries or post-hoc point repair. Constrain the full predicted chunk and report unused-tail violations separately.

These decisions establish the direction. They do not yet authorize implementation, tests, data generation or experiments.

## Research question and learning value

> Can a Riemannian flow-matching model generate learned pointing-motion sequences that satisfy previously unseen waypoint constraints through a generation-time geometric CBF layer, while retaining useful trajectory structure?

The learning component models observation-conditioned, ordered future position chunks. Longer motions emerge from repeated prediction and partial execution, following RFMP. Merely fitting an analytic point-to-goal attraction field would offer weak evidence of learned motion structure.

The applicant selected **LASA LShape only** for initial trials. Normalize and project recorded positions onto S², referring to the RFMP experiment. Train without the test-time forbidden cone, then introduce or move that cone during Phase 2 evaluation. Inherit documented RFMP settings; explicitly resolve under-specified mapping and split details in the specification. Do not add augmentation as if it were a reported paper decision.

See [the data-source comparison](data_options.md). The selected source supplies seven original recordings. Extracting multiple chunks/context pairs creates more training examples, not more independent demonstrations. The initial result should be presented as an RFMP method reimplementation on the LShape subset, not a reproduction of all paper experiments or broad generalization to robot hardware.

## Agreed two-phase development structure

**Phase 1 — RFMP reimplementation, no safety.** Follow the inherited settings below for LASA positions on S². Validate both generated chunks and receding-horizon motion reproduction. Preserve the model checkpoint, exact split indices and split unit, preprocessing, configuration, rollout initialization and evaluation random states. Check manifold adherence, motion fidelity and roughness; report goal error rather than imposing it through endpoint pinning. Exact acceptance criteria and test boundaries will be agreed in the spec.

**Method-design status:** Phase 1's method is settled. Under-specified reproduction details are explicit specification items, not permission to replace the method or import proposed Phase 2 mechanisms. The next design stage is Phase 2; see its [concrete methodology draft](methodology_phase2.md).

**Phase 2 — safety inside generation.** The approved structure adds terminal-recovery steering directly to the same RFMP chunk sampler and retains replanning. It permits a frozen-model comparison against Phase 1. Use the same initial observations and random-seed schedule, and the same source samples for matched single-chunk comparisons. In multi-step rollouts, steered and nominal histories can diverge, so observation conditions need not remain identical. Do not retrain or change preprocessing to obtain an apparent safety improvement. A separate complete-trajectory generator is outside this selected structure. Record violations, motion fidelity/roughness, interventions, runtime and failure cases. Numerical recovery and evaluation details remain under design discussion.

Each phase proceeds through approved vertical tickets and TDD. Do not mix safety changes into Phase 1 or begin Phase 2 with an unvalidated nominal generator. This structure does not authorize implementation before proposal approval.

Use small, coherent Git commits for approved work. Preserve the approved design/specification, and record a Phase 1 baseline commit before Phase 2 so safety changes can be audited independently. Keep checkpoints and datasets outside ordinary Git history by default; record their provenance, configuration and identifying hashes in reproducibility records. No remote/push is authorized merely by local version-control setup.

## Inherited Phase 1 settings

Source: [original RFMP paper, Sections III–IV](https://arxiv.org/html/2403.10672v1#S3). These are selected method settings for our LShape trial, not evidence of completed work.

| Item | Phase 1 choice |
| --- | --- |
| Data | Seven LShape recordings, resampled to the paper's 200 time steps per recording |
| Learned sample | Future position chunk on a product of S² factors |
| Conditioning | Reference position `o_(τ-1)`, earlier context `o_c`, and separation `τ-c`; context selected as described in the paper |
| Prediction/execution | Reported prediction horizon 8 and execution horizon half; precise point/transition indexing must be fixed consistently in the spec |
| Source | Wrapped Gaussian at the north pole, reported scale σ=0.5; repeat one sampled source point across the chunk |
| Target path | Coordinatewise geodesic conditional flow matching |
| Model | MLP, reported five layers and 64 hidden units, Swish with learnable parameter |
| Training | Adam, learning rate 1e-4; EMA decay 0.999; 200 epochs; select best validation model |
| Split | Reported 80/10/10; split unit is not established by the accessible paper description |
| Integration | Riemannian Euler; numerical step count must be resolved from sources or declared as our choice |
| Rollout | Generate a chunk, use its initial execution portion as desired positions, update observations and replan |
| Endpoints | No added hard start/goal pinning and no extra explicit final-goal conditioning |

The initial study remains LShape only. The paper's other families, horizon sweeps, image conditioning, Euclidean comparison and diffusion baseline are not silently added to the agreed small-project scope. Any omitted experiments must be clear when describing the reproduction. The replicated source prior lies on a repeated-point subset of the chunk space; preserve it for reproduction and disclose changes rather than silently substituting independent per-waypoint noise.

**Reproduction gaps:** the exact planar normalization/sphere mapping, split unit, layer-count convention, rollout bootstrap/context handling and integration resolution require source clarification or explicit specification choices. An 80/10/10 split cannot be interpreted as an exact whole-demonstration partition of only seven recordings. A grouped-demo split would be a declared deviation; a window split must not be described as held-out-recording generalization. Keep transforms of a recording traceable to their source.

## What one FM sample contains

Let

```text
X_s = [x_τ(s), x_(τ+1)(s), ..., x_(τ+H)(s)],       x_i(s) in S².
```

`s` is FM generation time. `τ` is the current rollout index; `i` indexes desired positions within the predicted chunk. The displayed inclusive indexing follows the paper's notation; the spec must settle whether the horizon parameter counts positions or transitions. Each integration step updates the candidate chunk jointly. At the end of generation, only its initial execution portion advances the rollout; intermediate FM candidates are not executed motions.

Observation conditioning initializes reproduction from a supplied position/history. It does not clamp a generated chunk's first or last position. The earlier hard-start/goal recommendation is superseded for Phase 1. Our direction sequences serve as desired-position commands; they are not angular-velocity commands. [LASA implementation review](docs/references/lasa_implementation_comparison.md)

SAD-Flower's complete state/action planning and its endpoint conditioning remain reference material for Phase 2 generation-time control. They must not be imported into Phase 1 as if they were RFMP decisions. [SAD-Flower](https://arxiv.org/html/2511.05355v3#S3)

## Proposed model and manifold geometry

Construct RFM training interpolations coordinatewise using sphere geodesics. Sum component errors using the product Riemannian metric. Use the paper's MLP on the joint chunk and conditioning, producing one tangent vector per generated position, projected into its tangent space:

```text
P_x = I - xxᵀ
V_theta,i(s,X,o) = P_x_i F_theta,i(s,X,o)
```

Here `o` is RFMP's observation/context conditioning. Sphere exp/log formulas, coincident points, antipodal ambiguity and target derivatives require explicit handling in the specification. Do not introduce hard endpoint masks. [Riemannian FM](https://arxiv.org/abs/2302.03660)

SRFMP is outside the selected Phase 1 reproduction and is not a mandatory additional model. Its stability concerns the generative distribution, not robot task convergence. An approximate learned field and its CBF-corrected version do not automatically inherit exact convergence. [Detailed reading](docs/references/flow_matching_and_stability.md)

## Generation-time geometric CBF layer

**Selected-filter update:** the applicant selected the body-coordinate QP `min_(Omega_i) (1/2)||Omega_i-Omega_theta,i||²` subject to `b_i^T Omega_i>=-phi(s)h_i`, with `b_i=-e3×(R_i^T c)`, `h_i=cos(theta_int)-c^T R_i e3`, and `Omega_theta,i=R_i^T(x_i×v_theta,i)`. Use the normalized SO(3) metric and horizontal auxiliary frame, preserving the S² RFMP model. The canonical derivation and geometric update are in [methodology.md](methodology.md). The S² formulas below are its equivalent projected description, not an alternative selected filter. Numerical settings and frame initialization remain unresolved; specification and implementation remain on hold.

The generated sequence follows

```text
dX_s/ds = V_theta(s,X_s,o) + U_s.
```

For a static forbidden direction `c∈S²` and cone half-angle `theta`, each generated position has

```text
h_i(X) = cos(theta) - cᵀx_i
a_i = grad_S² h_i = -(I-x_i x_iᵀ)c.
```

The intended constraint is `angle(x_i,c)>=theta`. This reverses the sign of the geometric CBF paper's keep-in satellite cone.

The applicant approved a slightly expanded internal cone. For steering, use `theta_internal=theta+delta`, `delta>0`, in the barrier formulas; retain the requested `theta` for reported clearance and the final safety check. The margin magnitude is a specification item, not a new physical exclusion requirement.

For the selected terminal-recovery design, the SAD-Flower-inspired condition is

```text
a_iᵀ(V_theta,i + U_i) >= -phi(s) h_i.
Example paper schedule: phi(s) = c_gain/(1-s)^2, c_gain > 0.
```

For one independent cap constraint per waypoint, an unbounded minimum-norm tangent correction has a closed-form solution:

```text
U_i = max(0, -(a_iᵀV_theta,i + phi(s) h_i)/||a_i||²) a_i.
```

Handle the zero-gradient branch explicitly. This simple, separable correction is attractive under the time budget, provided no additional coupled constraints are silently assumed. It applies the geometric CBF paper's first-order bundle formulation; it does not reproduce torque-level backstepping. Under the approved Phase 2 structure it acts on RFMP position chunks. [Geometric CBF paper](https://arxiv.org/abs/2510.20202v1)

### Selected initialization and terminal objective

The applicant selected unconstrained source noise and final-generation waypoint recovery, following SAD-Flower. Do not replace this with a safe-prior restriction or a downstream trajectory-following filter without agreement. Unconstrained noise here means unconstrained by the forbidden cone; samples and integration still belong on the sphere/product manifold.

SAD-Flower uses an initial unsteered phase and a controlled phase with prescribed-time scheduling; the activation time is a later numerical design parameter. Its theorem assumes joint feasibility and uses a singular gain near terminal generation time. An ordinary constant-gain invariance CBF does not alone establish finite-time recovery from unsafe source waypoints. [SAD-Flower Sections 5.2–5.3](https://arxiv.org/html/2511.05355v3#S5)

The finite-step implementation must specify terminal stopping, residual tolerances and failure reporting. The selected internal forbidden-cone margin provides room for recovery error but is not an established discrete safety guarantee; final positions must still be checked against the actual cone. At the forbidden center, the spherical barrier gradient vanishes while an unsafe-recovery inequality can demand a positive derivative, so recovery feasibility must not be asserted for every source sample. The applicant selected stopping and counting a failed rollout if the next execution portion contains unsafe directions. Unused-tail violations and numerical failures must be reported separately; do not resample to conceal them.

For a chunk-based extension, the supplied current direction should already be safe for any claimed safe rollout. Making the generated chunk safe cannot repair the previously supplied current direction or guarantee that the connection to the first commanded position avoids the cone. The claim sought concerns generated positions at the end of FM generation, not intermediate candidates or connecting arcs. No fixed physical endpoint constraints are part of Phase 1.

## What the project will and will not establish

Evaluate generated-position clearance, sphere norm/tangency errors, rollout terminal-goal error, demonstration/motion fidelity, interventions and runtime. Distinguish a chunk's last point from the final task goal; intermediate chunks are not supposed to reach that goal. Also measure roughness or adjacent angular jumps so safety obtained by destroying useful motion structure is visible.

Apply the same execution acceptance/stopping check to nominal and steered Phase 2 rollout comparisons. Report pre-acceptance unsafe proposals, unsafe execution-portion rejections, whole-chunk violations, rollout completion and numerical failures. Zero unsafe executed points produced by stopping is not itself evidence of successful CBF generation; stopped runs remain failures in the overall accounting. Preserve Phase 1's original unguided reproduction outputs separately.

Connecting arcs can enter the cap even when every waypoint is safe. We will explicitly report that limitation. A diagnostic of interpolated clearance is recommended if inexpensive, but continuous-path constraint enforcement is not an agreed core requirement. Geometry-preserving integration does not remove this gap.

Direction-only trajectories do not include SAD-Flower's physical state/action transition model or consistency CLF. Do not claim dynamic consistency, torque feasibility or physical closed-loop safety. Similarly, stable generation and exact planned endpoints are distinct from a robot successfully executing the plan.

## Comparisons and outputs

Recommended core comparisons:

1. Unfiltered Riemannian FM sequence generator.
2. The same trained generator with generation-time geometric CBFs, using matched seeds and source samples.
3. A simple geometric reference or post-hoc waypoint repair baseline, if it adds a clear comparison within the budget. Any repair must be disclosed and must not be used to conceal residual violations of the proposed generator.

Optional comparisons include stricter/new cone locations. Adding SRFMP or another model is outside Phase 1's selected reproduction and requires a scope decision. Decide metrics before running experiments. Preserve failed generations and rejected samples in the accounting.

Proposed outputs: reproducible source/configuration, a visualization of a candidate sequence changing during FM generation, a final-waypoint animation with the arc-safety limitation visible, evaluation plots/table and a short technical note. A CV entry must describe work actually completed and understood by the applicant, with no invented improvement percentages or guarantees.

## Paper resources checked

| Reference | Verified resource | Practical implication |
| --- | --- | --- |
| RFMP/SRFMP | [Authors' project page](https://sites.google.com/view/rfmp); paper/video available; official code, custom dataset and checkpoint not verified | Use the paper's construction; avoid dependence on an unavailable full reproduction package |
| Geometric CBFs | [Author-owned repository](https://github.com/mzdesa/Geometric_CBF), sphere/satellite scripts; license/dependencies not verified | Use theory; inspect licensing before adapting code |
| SAD-Flower | [Author repository](https://github.com/TzuYuan107/sad-flower), MIT; trajectory constraint machinery | Reference its generation-time control design; full MuJoCo/D4RL reproduction is outside scope |
| General RFM | [Official Meta repository](https://github.com/facebookresearch/riemannian-fm), archived, CC BY-NC 4.0 | Useful attributed geometry/training references; avoid recreating the entire old environment |

Detailed paper readings: [flow matching/stability](docs/references/flow_matching_and_stability.md), [geometric safety/SAD-Flower](docs/references/manifold_safety_references.md). No reference code was installed or executed. Existing conda environments have PyTorch/pytest metadata, but working imports and compute availability remain to be checked after approval.

## Time budget and workflow

| Stage | Proposed ceiling |
| --- | ---: |
| Paper research, grilling and proposal agreement, including the elapsed discussion window | 5 h |
| Specification, approved tickets and test-boundary agreement | 1 h |
| Geometry/data and a first end-to-end TDD slice | 2 h |
| Nominal sequence-model training and learning validation | 2 h |
| Generation-time CBF and numerical handling | 3 h |
| Matched evaluation and stress cases | 1 h |
| Visualizations, report and application evidence | 2 h |
| Contingency | 2 h |
| **Maximum total project work** | **18 h** |

Approved project hard stop: **30 October 09:45 China time, or earlier when the 18-hour total budget is reached**, retaining the rest of the day for application preparation. Research began about 15:58 China time on 29 October. At the 20:47 scheduling check, roughly 4 h 49 min had elapsed including discussion; this is a conservative planning window, not a measured active-work log. The revised allocation reserves 5 h for preparation and 13 h for subsequent stages. Do not consume the entire budget merely because it is available.

Follow **grilling → approved proposal → specification → approved vertical-slice tickets → TDD at agreed boundaries**. Phase 1's RFMP method, Phase 2's same-chunk/replanning structure, an internal angular safety margin and the execution-portion stopping rule are selected. Hard endpoint pinning and a separate whole-trajectory model are outside that structure. The applicant approved this proposal, then requested standalone and applicant review of [the consolidated methodology](methodology.md) before any specification or tickets. That latest instruction is the current gate. No project implementation, tests, generated data, model training or experiments are approved yet.
