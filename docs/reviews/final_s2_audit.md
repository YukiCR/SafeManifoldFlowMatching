# Final direct-S² methodology audit

29 October 2026. Snapshot: `f30e1f9996a6c6ddfdf24d2c6b5581ba3d293a11`, initially clean working tree. Canonical document: `methodology.md`; consistency checks: `methodology_phase2.md`, `proposal.md`, project `AGENTS.md` and `README.md`, plus the parent application README. Analytic review only: no new reference search, numerical experiments, implementation, specification or tickets. I derived the gradient/QP and recovery cases first, then consulted the earlier `mathematics.md` review; this report does not independently reverify paper-reported RFMP settings.

**Verdict: sound for the explicitly limited empirical study; no methodology blocker found.** The selected computation is intrinsic to S²/product S² under the stated round metric. It requires no SO(3) frame, roll variable or Lie-algebra lift. The latest applicant instruction can therefore advance Phase 1 to specification and the agreed ticket/test-interface approval workflow. This audit does not grant implementation approval independently of that workflow. Phase 2 remains deferred until a validated, frozen Phase 1 baseline and its subsequent authorization.

## Independent geometric check

For `M=(S²)^m`, the documented tangent spaces and metric `g_X(V,W)=sum_i v_i^T w_i` are correct. Per-factor projection represents round-metric tangent projection; it does not replace the product manifold by one large sphere. The conditional-geodesic target derivative and projected model output are both based at `X_s`, so the metric regression loss subtracts vectors in the same fiber. Factorwise sphere exponential Euler is geometric integration. Correct sphere membership alone does not prove a barrier condition, and a retraction update must be identified separately. Intrinsic position distances and the stated transport requirement for cross-point velocity comparisons are appropriate diagnostics.

For unit `c,x` and `h=cos(theta_int)-c^T x`,

```text
a=grad h=-(I-xx^T)c,
x^T a=0,
g_x(a,a)=1-(c^T x)^2,
dh[v]=g_x(a,v).
```

Thus moving along `a` increases clearance; the keep-out sign is correct. Set `b=g_x(a,v_theta)+phi*h`. If `a!=0`, projecting the nominal tangent velocity onto the feasible tangent half-space gives

```text
v_star=v_theta+max(0,-b/g_x(a,a))*a.
```

This is the unique minimum-change solution under the chosen round metric. The product objective and one independent cap constraint per waypoint separate despite the nominal network coupling the chunk. This conclusion assumes unbounded tangent controls and no added coupled constraints. The ambient dot-product implementation has the stated intrinsic meaning and needs no moving frame.

The activation bypass is correct: imposing the QP with `phi=0` would still restrict the nominal velocity. At `a=0`, the scalar feasibility test is essential. With positive gain, `x=c` is unsafe and infeasible, whereas `x=-c` is safe and permits the nominal velocity. Near-center corrections can grow as `phi*(1-cos(theta_int))/r`; clipping the denominator neither solves infeasibility nor preserves the original inequality.

## Recovery, evaluation and scope

The text correctly treats the singular terminal schedule as an objective, not a finite-step guarantee. An admitted equality trajectory can remain internally unsafe at every `s<1`. Exponential integration preserves sphere membership in exact arithmetic but does not certify discrete safety or cure terminal stiffness. The approved internal margin has the correct sign: `h_actual=h_internal+cos(theta)-cos(theta_int)`. It can absorb a bounded residual only when such a bound is established; the actual-cone final check remains necessary.

The execution rule checks the complete next execution portion before advancing, rejects it as a whole, stops at the last accepted direction and counts failure without retries. Whole-chunk violations, unused-tail violations, numerical failures and pre-acceptance proposals are distinguished. Equal acceptance checks and retention of failures prevent stopping from masquerading as improved generation. Matched numerical protocols isolate guidance if Phase 2 changes the nominal integrator/grid. Frozen checkpoint, preprocessing, prior, horizons and replanning preserve the intended comparison; diverging rollout histories are acknowledged.

Useful detours, goal reaching and preserved fidelity are empirical outcomes. The filter may stall. Safe waypoints do not establish safe connecting arcs, including the first commanded connection; physical tracking, dynamic consistency and torque feasibility remain outside scope. These limitations are stated accurately.

## Blockers versus later specification choices

**Methodology blockers: none under the present claims and explicit failure allowance.** Universal recovery or continuous-path/physical safety claims would fail this audit; the selected method makes none.

Before Phase 1 implementation, resolve and disclose the recorded reproduction gaps: embedding, split unit, exact horizon indices, Gaussian parameter interpretation, network/input shapes, training/checkpoint conventions, rollout bootstrap/context/padding and numerical integration. Validation must cover autonomous replanning, not only teacher-conditioned chunks or loss. Seven recordings and the repeated-point diagonal prior constrain the claims; neither is silently converted into independent demonstrations or a full-dimensional product prior.

Before any Phase 2 implementation, specify activation, gain, internal margin, finite terminal grid, geometry/feasibility tolerances, near-zero handling and computation/failure limits; freeze evaluation scenarios, thresholds and source-draw pairing. These are ordinary specification decisions, not demands for tuning values at the method stage. Preserve the original Phase 1 baseline and do not implement Phase 2 prematurely.

**Minor documentation inconsistency, not a mathematical blocker:** `methodology_phase2.md`'s last paragraph still says specification/tickets remain on hold, and `proposal.md`'s workflow ending and the parent application README retain the older review hold. Their updated openings, the canonical methodology and project AGENTS explicitly record conditional Phase 1 progression after this audit. Refresh those stale status sentences when recording the gate outcome; they should not reinstate the superseded hold or authorize Phase 2.

The closed form keeps the extension modest, but obtaining and validating Phase 1 remains the main practical dependency. Respect the 18-hour total including preparation and the hard stop of 30 October 2026 09:45 China time; this pass does not promise that both phases fit the remaining time. Historical SO(3) reports remain historical only.
