# Phase 2 methodology proposal

29 October 2026. **Final direct-S² method selected; Phase 2 implementation remains deferred. The latest instruction conditionally authorizes Phase 1 after the final method re-audit and workflow gates.** The applicant approved retaining RFMP's same position-chunk horizons and replanning loop, steering each FM generation solve while freezing the Phase 1 model; a slightly expanded internal forbidden cone; and stopping on an unsafe next execution portion. Exact numerical settings and evaluation thresholds remain unresolved. Undocumented Phase 1 reproduction details must be explicit.

## Objective and scope

Test whether generation-time geometric CBF steering improves forbidden-direction avoidance while retaining useful learned motion. Preserve Phase 1's RFMP checkpoint, preprocessing, observation conditioning, prior, prediction/execution horizons and replanning loop. Do not add goal pinning, a goal CLF, new training data or a second learned model to this proposed core.

Start with one static forbidden spherical cap per rollout, representing a sensor/tool direction exclusion. Its center and angle are supplied to the safety layer, not added to the frozen network's inputs. Apply the barrier to **every predicted position in the chunk**, including positions beyond the portion about to be executed. This is a proposed small adaptation of SAD-Flower's generation-time control to RFMP's product-sphere chunks, not a reproduction of all SAD-Flower mechanisms.

## Two time axes and the controlled system

At physical rollout index `k`, keep the observation history `o_k` fixed throughout one generation solve. Let `X_s=(x_1(s),...,x_m(s))` be the predicted direction chunk; `s∈[0,1]` is FM generation time. The source chunk is drawn exactly as in Phase 1, without rejecting samples inside the forbidden cone.

```text
dX_s/ds = V_theta(s, X_s | o_k) + U_s.
```

Both the nominal field and projected correction belong to the product tangent space. The selected Phase 2 update is sphere exponential Euler; preserve the original Phase 1 sampler and add a matched-update nominal comparison if its solver differs. A generation step changes a candidate chunk; it does not advance the robot's physical rollout.

After generation, check every direction in its RFMP execution portion against the actual requested cone before advancing. If that portion passes, it advances the position-command rollout; update observation history and repeat. If any direction in that portion is unsafe, reject the entire portion, keep the last accepted direction and count a failed rollout. The virtual correction `U` is not a physical angular velocity or torque command.

## Final selected geometric CBF directly on S²

The applicant's final decision supersedes the SO(3) lift: keep all computation directly on S² with its round metric. For requested angle `theta`, internal angle `theta_int=theta+delta` and unit forbidden center `c`,

```text
h_actual,i = cos(theta)-c^T x_i,
h_i = cos(theta_int)-c^T x_i,
a_i = grad_S² h_i = -(I-x_i x_i^T)c.
```

During guidance, minimize `(1/2)||v_i-v_theta,i||²_(g_(x_i))` over `v_i in T_(x_i)S²`, subject to `dh_i[v_i]=g_(x_i)(a_i,v_i)>=-phi(s)h_i`. The exact single-cap solution for `a_i!=0` is

```text
lambda_i = max(0, (-g_(x_i)(a_i,v_theta,i)-phi(s)*h_i)/g_(x_i)(a_i,a_i)),
v_star,i = v_theta,i+lambda_i*a_i,
x_i^+ = Exp_(x_i)(ds*v_star,i).
```

Before activation bypass the QP, rather than imposing it with zero gain. At zero gradient, retain nominal only if the inequality is already feasible; otherwise report infeasibility. Do not cure infeasibility by denominator clipping. No rotation frames, Lie-algebra rates or roll variables are used. The nominal network, source prior, observation conditioning and replanning remain unchanged. See the [core methodology](methodology.md) for geometric meanings and limitations.

## Terminal recovery and finite-step behavior

Follow SAD-Flower's distinction between an initial nominal generation interval and a controlled interval. A reference schedule is `phi(s)=gamma/(1-s)^2`, activated at `s_on`. Intermediate candidates may be unsafe; the objective concerns the returned chunk. Gain, activation and integration resolution belong in the specification and must be recorded.

For an unsafe initial barrier, the equality solution `h(s)=h(s_on) exp(-integral(phi))` can stay negative for every `s<1`. The singular terminal argument is therefore not an exact finite-step certificate. Do not evaluate the singular expression at `s=1` or silently report its ideal theorem as observed safety.

**Approved margin design:** steer against a slightly expanded internal cap `theta_internal=theta+delta`, with `0<theta<theta+delta<pi`, and evaluate safety against the actual requested cap. Substitute `theta_internal` in the filter's barrier formulas. The numerical stopping protocol and exact margin remain to be specified. If the internal barrier residual is bounded below by `-eta`, then

```text
h_actual >= cos(theta) - cos(theta+delta) - eta.
```

This identity explains the margin; it does not establish a discrete residual bound. The returned sample must still be checked directly. Declare stopping time, margin, tolerance and guidance parameters before final evaluation. No undisclosed post-hoc waypoint repair or success-only rejection sampling.

At `x_i=c`, the barrier gradient vanishes while recovery can require a positive derivative; the constraint is infeasible there. A zero-gradient constraint that is already satisfied instead needs no correction. Treat zero/near-zero gradient cases explicitly. Adding a denominator epsilon alone does not solve the original inequality. Numerical failure or invalid sampler output must be reported rather than hidden as successful recovery.

**Approved failure policy:** if any direction in the next execution portion violates the actual cone, reject that entire portion before advancing, stop at the last accepted direction and count a rollout failure. Do not execute its safe leading subset, retry from fresh noise, or repair its points after generation. A stopped rollout is not a completed safe motion. Continue to impose barriers on all predicted positions; violations confined to the unused tail are recorded as whole-chunk constraint failures and do not alone trigger the execution stopping rule. Invalid geometry or numerical failure receives its own failure label.

## Evaluation that isolates the extension

Use two complementary comparisons:

1. **Matched single-chunk generation:** identical checkpoint, observation/context, source chunk and integration budget; guidance is the difference. Measure final constraint violations/clearance, displacement from nominal output, motion roughness, intervention magnitude, constraint residuals and runtime.
2. **Receding-horizon rollouts:** identical initial history, scenario and random-seed schedule. Evaluate executed-position clearance, motion fidelity, terminal goal error, goal-reaching rate, stalls/stops and runtime. After steering changes a rollout, later observation histories can differ; do not describe those later conditions as identical.

For the Phase 2 comparison, use the same execution acceptance/stopping check for nominal and steered rollouts. Keep Phase 1's original reproduction outputs separately. Report violations **before** acceptance, unsafe execution-portion rejection rate, whole-chunk violations, completion and goal-reaching, and numerical failures. The acceptance check is separate from CBF steering: zero unsafe executed points obtained by stopping is not by itself evidence that the generator improved. Keep stopped runs in the denominator and do not compare fidelity only on favorable survivors.

If safety numerics require a different time grid or stopping point from the validated Phase 1 sampler, include an unsteered comparison with that same numerical protocol. Retain the original Phase 1 result separately. Otherwise truncation or extra integration effort could be mistaken for an effect of CBF steering. Record the change rather than overwriting the original baseline configuration.

Freeze cap scenarios and success thresholds before final comparisons. Use a cap that intersects the nominal LShape route while leaving the supplied start and demonstrated goal outside the internal cap. Include a no-conflict case to reveal unnecessary distortion. Keep development/tuning scenarios distinguishable from final evaluation; do not retain only favorable cone placements. Additional cap positions are stress cases, not additional training families.

Use terminal goal error as an outcome, not as a hard safety constraint or an implied guarantee. A safe returned chunk may distort the motion, stall near the boundary or fail to reach the goal. Account for those outcomes jointly with avoidance.

## Claims and outstanding decisions

The intended result concerns **sampled directions returned by the generator and the discrete position-command rollout**. Connecting arcs, including the connection from the supplied current direction to the next command, can remain unsafe. No dynamic-consistency, physical tracking or torque-level guarantee is claimed. The supplied initial direction cannot be retroactively repaired by filtering future generated positions.

**Approved decisions:** retain RFMP's position-chunk horizons, observation conditioning and replanning loop; use the selected direct-S² tangent QP with the frozen model; use a slightly expanded internal cap and measure actual-cone safety; stop and count failure when the next execution portion is unsafe. Do not replace the sampler with a separate complete-trajectory model. The proposal and final direct-S² method are approved and the method audit passed. Phase 1 specification/tickets may progress through the agreed approval workflow; Phase 2 implementation remains deferred. No implementation, tests or experiments have been started.
