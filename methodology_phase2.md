# Phase 2 methodology proposal

29 October 2026. **Methodology under design discussion; not an approved specification or implementation.** The applicant approved retaining RFMP's same position-chunk horizons and replanning loop for Phase 2, steering each FM generation solve while freezing the Phase 1 model. A slightly expanded internal forbidden cone is also approved; its margin magnitude remains a specification item. Failure handling and remaining numerical/evaluation choices are still proposed. Undocumented Phase 1 reproduction details remain specification items.

## Objective and scope

Test whether generation-time geometric CBF steering improves forbidden-direction avoidance while retaining useful learned motion. Preserve Phase 1's RFMP checkpoint, preprocessing, observation conditioning, prior, prediction/execution horizons and replanning loop. Do not add goal pinning, a goal CLF, new training data or a second learned model to this proposed core.

Start with one static forbidden spherical cap per rollout, representing a sensor/tool direction exclusion. Its center and angle are supplied to the safety layer, not added to the frozen network's inputs. Apply the barrier to **every predicted position in the chunk**, including positions beyond the portion about to be executed. This is a proposed small adaptation of SAD-Flower's generation-time control to RFMP's product-sphere chunks, not a reproduction of all SAD-Flower mechanisms.

## Two time axes and the controlled system

At physical rollout index `k`, keep the observation history `o_k` fixed throughout one generation solve. Let `X_s=(x_1(s),...,x_m(s))` be the predicted direction chunk; `s∈[0,1]` is FM generation time. The source chunk is drawn exactly as in Phase 1, without rejecting samples inside the forbidden cone.

```text
dX_s/ds = V_theta(s, X_s | o_k) + U_s.
```

Both the nominal field and correction belong to the product tangent space. Preserve the paper's manifold integration method for nominal and steered comparisons. A generation step changes a candidate chunk; it does not advance the robot's physical rollout.

After generation, inspect and return the candidate. Only its RFMP execution portion advances the position-command rollout. Update observation history and repeat. The virtual correction `U` is not a physical angular velocity or torque command.

## Barrier and minimum-change correction

For unit forbidden direction `c` and physical exclusion half-angle `theta`, define

```text
h_i = cos(theta) - c^T x_i,
P_i = I - x_i x_i^T,
a_i = grad_S² h_i = -P_i c.
```

Thus `h_i>=0` means the generated direction lies outside the forbidden cone. At each controlled generation step, solve

```text
minimize_U  (1/2) sum_i ||U_i||²
subject to a_i^T (V_i + U_i) >= -phi(s) h_i,
           U_i in T_(x_i) S².
```

One cap and independent tangent corrections make the constraints separable. For nonzero `a_i`, the exact minimum-norm solution is

```text
U_i = max(0, -(a_i^T V_i + phi(s) h_i)/||a_i||²) a_i.
```

Although this correction is separable, the learned nominal field still sees the joint chunk. This formulation uses no correction-speed bound and establishes no physical actuator feasibility. Its derivation follows the [geometric CBF framework](https://arxiv.org/abs/2510.20202v1); the terminal-recovery schedule follows [SAD-Flower, Section 5](https://arxiv.org/html/2511.05355v3#S5).

## Terminal recovery and finite-step behavior

Follow SAD-Flower's distinction between an initial nominal generation interval and a controlled interval. A reference schedule is `phi(s)=gamma/(1-s)^2`, activated at `s_on`. Intermediate candidates may be unsafe; the objective concerns the returned chunk. Gain, activation and integration resolution belong in the specification and must be recorded.

For an unsafe initial barrier, the equality solution `h(s)=h(s_on) exp(-integral(phi))` can stay negative for every `s<1`. The singular terminal argument is therefore not an exact finite-step certificate. Do not evaluate the singular expression at `s=1` or silently report its ideal theorem as observed safety.

**Approved margin design:** steer against a slightly expanded internal cap `theta_internal=theta+delta`, with `0<theta<theta+delta<pi`, and evaluate safety against the actual requested cap. Substitute `theta_internal` in the filter's barrier formulas. The numerical stopping protocol and exact margin remain to be specified. If the internal barrier residual is bounded below by `-eta`, then

```text
h_actual >= cos(theta) - cos(theta+delta) - eta.
```

This identity explains the margin; it does not establish a discrete residual bound. The returned sample must still be checked directly. Declare stopping time, margin, tolerance and guidance parameters before final evaluation. No undisclosed post-hoc waypoint repair or success-only rejection sampling.

At `x_i=c`, the barrier gradient vanishes while recovery can require a positive derivative; the constraint is infeasible there. A zero-gradient constraint that is already satisfied instead needs no correction. Treat zero/near-zero gradient cases explicitly. Adding a denominator epsilon alone does not solve the original inequality. Report failed or unresolved generations and do not advance a rollout with a chunk that failed its declared acceptance check. **Pending failure-policy choice:** stop the rollout at its last accepted direction and count a failure (recommended), or retry from fresh noise with a fixed attempt limit and full attempt accounting. A stopped rollout counts as a failure, not a completed safe motion.

## Evaluation that isolates the extension

Use two complementary comparisons:

1. **Matched single-chunk generation:** identical checkpoint, observation/context, source chunk and integration budget; guidance is the difference. Measure final constraint violations/clearance, displacement from nominal output, motion roughness, intervention magnitude, constraint residuals and runtime.
2. **Receding-horizon rollouts:** identical initial history, scenario and random-seed schedule. Evaluate executed-position clearance, motion fidelity, terminal goal error, goal-reaching rate, stalls/stops and runtime. After steering changes a rollout, later observation histories can differ; do not describe those later conditions as identical.

If safety numerics require a different time grid or stopping point from the validated Phase 1 sampler, include an unsteered comparison with that same numerical protocol. Retain the original Phase 1 result separately. Otherwise truncation or extra integration effort could be mistaken for an effect of CBF steering. Record the change rather than overwriting the original baseline configuration.

Freeze cap scenarios and success thresholds before final comparisons. Use a cap that intersects the nominal LShape route while leaving the supplied start and demonstrated goal outside the internal cap. Include a no-conflict case to reveal unnecessary distortion. Keep development/tuning scenarios distinguishable from final evaluation; do not retain only favorable cone placements. Additional cap positions are stress cases, not additional training families.

Use terminal goal error as an outcome, not as a hard safety constraint or an implied guarantee. A safe returned chunk may distort the motion, stall near the boundary or fail to reach the goal. Account for those outcomes jointly with avoidance.

## Claims and outstanding decisions

The intended result concerns **sampled directions returned by the generator and the discrete position-command rollout**. Connecting arcs, including the connection from the supplied current direction to the next command, can remain unsafe. No dynamic-consistency, physical tracking or torque-level guarantee is claimed. The supplied initial direction cannot be retroactively repaired by filtering future generated positions.

**Approved decisions:** retain the same RFMP position-chunk horizons, observation conditioning and replanning loop; add generation-time correction using the frozen Phase 1 model; use a slightly expanded internal cap and measure actual-cone safety. Do not replace the sampler with a separate complete-trajectory model. Remaining design discussion covers the cone/scenario setup, failure accounting and evaluation criteria; exact numerical values, including margin magnitude, belong in the approved specification. No implementation, tests or experiments have been started.
