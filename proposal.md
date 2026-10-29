# Proposal: generation-time geometric CBFs for Riemannian motion sequences

29 October 2026. **Design stage; overall proposal and implementation approval pending.**

## Purpose

Develop a compact, explainable project demonstrating **learning, manifold geometry, safety control and robotics** for the PhD application. A robotic camera/sensor/tool axis must produce a sequence of pointing directions on S² toward a target while respecting a forbidden angular cone at its generated waypoints.

Primary references are **RFMP/SRFMP**, **From Bundles to Backstepping**, and **SAD-Flower**. Chen/Lipman's general Riemannian FM supplies foundational geometry and training machinery.

## Agreed decisions and boundaries

- Generate a **whole trajectory**, rather than treating the FM integration trace of a single sphere point as the robot motion.
- CBF correction acts **inside the FM generation process**. Downstream trajectory-following filtering is only a fallback if the preferred design cannot fit the time budget.
- Use S² pointing; full SO(3), visual perception, torque dynamics and hardware deployment are outside the current scope.
- **Connecting arcs can be unsafe.** Generated waypoint safety must not be reported as a guarantee for continuous interpolated motion.
- **No dynamic-consistency guarantee.** Sphere membership and waypoint constraints do not establish physical state/action consistency.
- Start the generated interior waypoints from **unconstrained sphere-valued noise** and recover waypoint safety by the end of generation, referring to SAD-Flower. Intermediate candidates may be unsafe. This replaces the earlier safe-initialization recommendation.
- Maximum project work: **18 hours**, preserving headroom for the 30 October application.
- Develop in two auditable phases: **Phase 1, manifold FM alone; Phase 2, add safety steering inside generation.** Establish a reproducible Phase 1 baseline before beginning Phase 2.
- Initial trials use **LASA LShape only**, mapped onto S². Do not expand to multiple families or switch to synthetic training data without agreement.
- Manage the project with its own Git repository, **SafeManifoldFlowMatching**, at `application/SafeManifoldFlowMatching/`.

These decisions establish the direction. They do not yet authorize implementation, tests, data generation or experiments.

## Research question and learning value

> Can a Riemannian flow-matching model generate learned pointing-motion sequences that satisfy previously unseen waypoint constraints through a generation-time geometric CBF layer, while retaining useful trajectory structure?

The learning component should model complete, ordered motion demonstrations, including variation in path shape. Merely fitting an analytic point-to-goal attraction field would offer weak evidence of sequence learning.

The applicant selected the **LShape family from LASA** for initial trials. Map the recorded planar sequences onto S² with documented, training-only preprocessing. Train without the test-time forbidden cone, then introduce or move that cone during Phase 2 evaluation. Split by original demonstration before any augmentation; transformed versions of the same recording must not leak across splits. Conditioning, augmentation and split details remain grilling decisions.

See [the data-source comparison](data_options.md). The selected LASA source provides human-drawn planar demonstrations requiring a documented sphere embedding. Because our samples are full sequences, seven demonstrations mean seven original sequence examples, not thousands of independent trajectories. The initial result should be presented as a small LShape pilot rather than broad generalization across skills or real robot pointing data.

## Agreed two-phase development structure

**Phase 1 — manifold FM only.** Establish the chosen dataset and preprocessing, a sphere/product-manifold model, training and generation. Evaluate learning quality and sequence structure without a safety layer. Preserve the model checkpoint, source-demo train/validation/test split, preprocessing configuration, generation settings and fixed evaluation noise samples. Baseline diagnostics should include manifold adherence and held-out trajectory fidelity, so merely placing outputs on the sphere is not mistaken for successful learning. Exact acceptance criteria and test boundaries will be agreed in the spec.

**Phase 2 — safety inside generation.** Reuse the validated Phase 1 checkpoint and paired evaluation samples. Add terminal-recovery steering for new forbidden cones, then compare filtered and unfiltered generations. In the core comparison, do not retrain the model or change data preprocessing to obtain the apparent safety improvement. Record terminal waypoint violations, changes in trajectory fidelity/roughness, interventions, runtime and failure cases. Keep the acknowledged connecting-arc and dynamic-consistency limitations explicit.

Each phase proceeds through approved vertical tickets and TDD. Do not mix safety changes into Phase 1 or begin Phase 2 with an unvalidated nominal generator. This structure does not authorize implementation before proposal approval.

Use small, coherent Git commits for approved work. Preserve the approved design/specification, and record a Phase 1 baseline commit before Phase 2 so safety changes can be audited independently. Keep checkpoints and datasets outside ordinary Git history by default; record their provenance, configuration and identifying hashes in reproducibility records. No remote/push is authorized merely by local version-control setup.

## What one FM sample contains

Let

```text
X_s = [x_0(s), x_1(s), ..., x_H(s)],       x_i(s) in S².
```

`s` is FM generation time. `i` indexes waypoints along the planned robot motion. Each FM integration step updates an entire candidate motion sequence. The **final candidate sequence** is the returned plan; intermediate candidates are not executed motions.

Recommend fixing `x_0=x_start` and `x_H=x_goal` and generating only the interior sequence on `(S²)^(H-1)`. Endpoint conditioning/pinning is a proposed design choice to confirm. It establishes planned endpoints, not physical closed-loop convergence.

RFMP Section IV-A generates an action horizon, and SAD-Flower Sections 3–5 generate complete state/action trajectories. Our direction sequences can serve as planned states or desired-direction commands. Their role must be stated explicitly; a manifold-valued action need not be an angular velocity. [RFMP/SRFMP](https://arxiv.org/html/2412.10855v3#S4.SS1), [SAD-Flower](https://arxiv.org/html/2511.05355v3#S3)

## Proposed model and manifold geometry

Construct RFM training interpolations coordinatewise using sphere geodesics. Sum component errors using the product Riemannian metric. A small sequence-aware model produces one tangent vector per generated waypoint, with each output projected into that waypoint's tangent space:

```text
P_x = I - xxᵀ
V_theta,i(s,X,o) = P_x_i F_theta,i(s,X,o)
```

Here `o` is the agreed start/goal/task conditioning. The model should see the sequence jointly rather than treating every waypoint as an unrelated training example. Sphere exp/log formulas, coincident points, antipodal ambiguity, endpoint pinning and target derivatives require explicit handling in the later specification. [Riemannian FM](https://arxiv.org/abs/2302.03660)

SRFMP provides a possible stability-oriented comparison through augmented pseudo-time and exponentially contracting conditional paths. Its stability concerns the generative distribution. An approximate learned field and its CBF-corrected version do not automatically inherit exact convergence. The supplied paper also has direction/tangent-anchor notation inconsistencies; derive targets from the intended path. Whether stable FM is mandatory or a time-boxed extension remains open. [Detailed reading](../research/flow_matching_and_stability.md)

## Generation-time geometric CBF layer

The generated sequence follows

```text
dX_s/ds = V_theta(s,X_s,o) + U_s.
```

For a static forbidden direction `c∈S²` and cone half-angle `theta`, each generated interior waypoint has

```text
h_i(X) = cos(theta) - cᵀx_i
a_i = grad_S² h_i = -(I-x_i x_iᵀ)c.
```

The intended constraint is `angle(x_i,c)>=theta`. This reverses the sign of the geometric CBF paper's keep-in satellite cone.

For the selected terminal-recovery design, the SAD-Flower-inspired condition is

```text
a_iᵀ(V_theta,i + U_i) >= -phi(s) h_i.
Example paper schedule: phi(s) = c_gain/(1-s)^2, c_gain > 0.
```

For one independent cap constraint per waypoint, an unbounded minimum-norm tangent correction has a closed-form solution:

```text
U_i = max(0, -(a_iᵀV_theta,i + phi(s) h_i)/||a_i||²) a_i.
```

Handle the zero-gradient branch and pinned endpoints explicitly. This simple, separable correction is attractive under the time budget, provided no additional coupled constraints are silently assumed. It applies the geometric CBF paper's first-order bundle formulation; it does not reproduce torque-level backstepping. [Geometric CBF paper](https://arxiv.org/abs/2510.20202v1)

### Selected initialization and terminal objective

The applicant selected unconstrained source noise and final-generation waypoint recovery, following SAD-Flower. Do not replace this with a safe-prior restriction or a downstream trajectory-following filter without agreement. Unconstrained noise here means unconstrained by the forbidden cone; samples and integration still belong on the sphere/product manifold.

SAD-Flower uses an initial unsteered phase and a controlled phase with prescribed-time scheduling; the activation time is a later numerical design parameter. Its theorem assumes joint feasibility and uses a singular gain near terminal generation time. An ordinary constant-gain invariance CBF does not alone establish finite-time recovery from unsafe source waypoints. [SAD-Flower Sections 5.2–5.3](https://arxiv.org/html/2511.05355v3#S5)

The finite-step implementation must specify terminal stopping, residual tolerances and failure reporting. A possible practical design is a tightened internal forbidden cone to retain a margin at the actual constraint; it remains a design proposal, not an established guarantee. At the forbidden center, the spherical barrier gradient vanishes while an unsafe-recovery inequality can demand a positive derivative, so recovery feasibility must not be asserted for every source sample. Near-degenerate cases and any retries/rejections must be visible in the evaluation.

If start/goal endpoints are pinned as proposed, both must be outside the forbidden cone; unsafe pinned endpoints would make the task infeasible. The claim sought is about the final generated waypoint sequence, not intermediate candidate safety or connecting arcs.

## What the project will and will not establish

Evaluate final waypoint clearance, sphere norm/tangency errors, planned endpoint accuracy, demonstration/sequence fidelity, interventions and runtime. Also measure roughness or adjacent angular jumps so safety obtained by destroying useful motion structure is visible.

Connecting arcs can enter the cap even when every waypoint is safe. We will explicitly report that limitation. A diagnostic of interpolated clearance is recommended if inexpensive, but continuous-path constraint enforcement is not an agreed core requirement. Geometry-preserving integration does not remove this gap.

Direction-only trajectories do not include SAD-Flower's physical state/action transition model or consistency CLF. Do not claim dynamic consistency, torque feasibility or physical closed-loop safety. Similarly, stable generation and exact planned endpoints are distinct from a robot successfully executing the plan.

## Comparisons and outputs

Recommended core comparisons:

1. Unfiltered Riemannian FM sequence generator.
2. The same trained generator with generation-time geometric CBFs, using matched seeds and source samples.
3. A simple geometric reference or post-hoc waypoint repair baseline, if it adds a clear comparison within the budget. Any repair must be disclosed and must not be used to conceal residual violations of the proposed generator.

Optional comparisons include stable versus ordinary RFM and stricter/new cone locations. Decide model variants and metrics before running experiments. Preserve failed generations and rejected samples in the accounting.

Proposed outputs: reproducible source/configuration, a visualization of a candidate sequence changing during FM generation, a final-waypoint animation with the arc-safety limitation visible, evaluation plots/table and a short technical note. A CV entry must describe work actually completed and understood by the applicant, with no invented improvement percentages or guarantees.

## Paper resources checked

| Reference | Verified resource | Practical implication |
| --- | --- | --- |
| RFMP/SRFMP | [Authors' project page](https://sites.google.com/view/rfmp); paper/video available; official code, custom dataset and checkpoint not verified | Use the paper's construction; avoid dependence on an unavailable full reproduction package |
| Geometric CBFs | [Author-owned repository](https://github.com/mzdesa/Geometric_CBF), sphere/satellite scripts; license/dependencies not verified | Use theory; inspect licensing before adapting code |
| SAD-Flower | [Author repository](https://github.com/TzuYuan107/sad-flower), MIT; trajectory constraint machinery | Reference its generation-time control design; full MuJoCo/D4RL reproduction is outside scope |
| General RFM | [Official Meta repository](https://github.com/facebookresearch/riemannian-fm), archived, CC BY-NC 4.0 | Useful attributed geometry/training references; avoid recreating the entire old environment |

Detailed paper readings: [flow matching/stability](../research/flow_matching_and_stability.md), [geometric safety/SAD-Flower](../research/manifold_safety_references.md). No reference code was installed or executed. Existing conda environments have PyTorch/pytest metadata, but working imports and compute availability remain to be checked after approval.

## Time budget and workflow

| Stage | Proposed ceiling |
| --- | ---: |
| Paper research, grilling and proposal agreement | 2 h |
| Specification, approved tickets and test-boundary agreement | 1 h |
| Geometry/data and a first end-to-end TDD slice | 3 h |
| Nominal sequence-model training and learning validation | 3 h |
| Generation-time CBF and numerical handling | 3 h |
| Matched evaluation and stress cases | 2 h |
| Visualizations, report and application evidence | 2 h |
| Contingency | 2 h |
| **Maximum total project work** | **18 h** |

Proposed hard stop is 30 October 10:00 China time or earlier, retaining the rest of the day for application preparation. Confirm the cutoff during grilling. Research for this proposal began about 15:58 China time on 29 October. Do not consume the entire budget merely because it is available.

Follow **grilling → approved proposal → specification → approved vertical-slice tickets → TDD at agreed boundaries**. Current open decisions include endpoint conditioning, preprocessing/splits/augmentation, mandatory model variants, evaluation thresholds and the hard stop. LASA LShape, Git management and terminal-recovery initialization are agreed. No project implementation, tests, generated data, model training or experiments are approved yet.
