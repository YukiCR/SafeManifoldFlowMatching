# Audit of the selected body-coordinate safety filter

29 October 2026. Reviewed snapshot: `6165a5c3974f4f11c8f4f42d71b9aca5122c782b`. Analytic/document review only; no specification, tickets, implementation, tests, numerical experiments or data preparation were performed. Line references below refer to that snapshot.

**Verdict: mathematical pass, with empirical/numerical feasibility still unproven.** The selected QP is a correct normalized-metric horizontal lift of the existing round-sphere minimum-change filter. The updated canonical method selects it unambiguously; it does not ask the applicant to choose again. I found no mathematical blocker or conflicting operative safety policy. The qualifications already recorded are necessary: the unsafe center can be infeasible, the singular schedule does not certify finite-step recovery, and waypoint checks do not certify connecting arcs.

## Prioritized findings

No high- or medium-priority issue requires changing the selected method. Two low-priority documentation clarifications would improve reading; neither blocks applicant methodology review.

1. **Clarify the axis of auxiliary-frame propagation.** In `methodology.md` §5, lines 140–142 and 195–197, frames are carried along each generation solve. Combined with the product factors and two-time-axis discussion in §3 (lines 31–55), the mathematics correctly gives one horizontal lift for each predicted waypoint as generation time varies. An explicit sentence could prevent a reader from inferring attitude reconstruction along physical waypoint indices: “Each frame is propagated in generation time for its own product factor; this does not prescribe roll continuity or parallel transport between successive commanded waypoints.” This is a terminology clarification, not an additional transport requirement, attitude output or learning task.

2. **Mark the review index's lift subsection as historical/preselection evidence.** `docs/reviews/README.md`, lines 37–39, still says “user-proposed” and describes the representation as recorded for applicant review without stating that the QP has since been selected. The canonical `methodology.md`, lines 138–176 and 201, and project `README.md`, line 27, already distinguish the selected method from the older candidate audit. A short index update could make the same distinction. Leave the historical report's original verdict/status intact. This is an index-status inconsistency only, not ambiguity in the operative method.

## Checked algebra and geometric meanings

**Barrier, sign and metric.** `methodology.md` §5, lines 114–155, correctly separates `h_actual=cos(theta)-c·x` from the internal filtering barrier `h=cos(theta_int)-c·x`. For `q=R^T c` and `hat(eta)w=eta×w`,

```text
dh_R[R hat(eta)] = -q·(eta×e3)
                 = (-e3×q)·eta = b·eta.
```

Thus the selected outside-of-cap sign is correct. Under `g_R(R hat(u),R hat(v))=u·v`, the gradient is exactly `R hat(b)`. The factor `1/2` in the Frobenius expression supplies that normalization. The internal/actual relationship is exactly `h_actual=h+cos(theta)-cos(theta_int)`; the stated margin inequality is conditional on a residual bound and does not invent such a bound.

**Nominal lift and optimizer.** Lines 158–191 retain the frozen direction-valued RFMP field. For tangent `v`, `Omega_theta=R^T(x×v)` is horizontal and projects to `v`, since `(x×v)×x=v`. Also `b=R^T(x×a)`, where `a=-(I-xx^T)c`; consequently `||b||=||a||` and `b·Omega_theta=a·v`. Projection onto the specified half-space therefore gives exactly

```text
lambda = max(0, (-b·Omega_theta-phi*h)/||b||²),
Omega_star = Omega_theta+lambda*b.
```

Both terms are horizontal, even though the optimization variable ranges over all of `R³`. No missing horizontal constraint changes this particular optimizer. Its projected velocity is `v+lambda*a`, and its intervention norm is the product-round-metric intervention norm. The cost and constraints separate across positions; dependence of the learned nominal field on the joint chunk does not destroy this pointwise separability. The tangent-bundle description and training loss in §§3–4 remain consistent with this geometry.

**Degenerate branches and activation.** Lines 187–189 correctly bypass the QP before activation; setting `phi=0` while retaining the inequality would impose `b·Omega>=0`. At `b=0`, feasibility is precisely `0>=-phi*h`. With positive gain, `x=c` has negative internal barrier and is infeasible, while `x=-c` has positive internal barrier and is feasible. Retaining the nominal rate only when feasible is the correct zero-gradient rule. Near-center thresholds, numerical limits and failure handling need later operational choices; clipping the denominator would not establish feasibility. Lines 205–209 correctly expose the coupled near-center and terminal-gain risks rather than claiming universal recovery.

**Source, gauge and integration.** Lines 191 and 195–199 correctly retain the Phase 1 sphere source and introduce no learned roll distribution. For an initial fiber rotation `R'=RQ`, `Qe3=e3`, the lift and barrier coordinates transform as `Omega_theta'=Q^T Omega_theta` and `b'=Q^T b`. Scalar residuals and the optimizer are invariant/covariant accordingly, so the projected pointing iterates are unchanged. This requires neither spatial rotation equivariance of RFMP nor a global smooth frame section. Holonomy is explicitly acknowledged.

For a frozen horizontal rate, the selected rotation update satisfies

```text
R exp(ds*hat(Omega_star)) e3
  = cos(ds*||v_star||)x
    + sin(ds*||v_star||)/||v_star|| * v_star
  = Exp_x(ds*v_star),
```

with the zero-rate limit understood. This is exponential Euler equivalence, not equivalence to normalized ambient Euler, every Riemannian integrator, or an exact time-varying ODE solve. The canonical text states these distinctions. The earlier `quotient_lift_independent.md` supplies compatible algebraic evidence; its candidate wording is historical rather than a competing current choice.

## Preservation, execution and claims

`methodology.md` §4, lines 57–96, preserves the inherited RFMP short-chunk/history/prior/replanning design, records reproduction gaps and requires a validated autonomous baseline before Phase 2. §5, line 197, and §7, lines 223–225, require a matched numerical-protocol unsteered comparison if the selected Phase 2 update, grid or stopping time differs from Phase 1. They also preserve the original Phase 1 artifact separately. This prevents a change of integrator or truncation from being credited to steering.

§6, lines 213–219, correctly gates advancement on the **entire next execution portion**, checked against the actual requested cone. One unsafe position rejects that complete portion, retains the last accepted direction and counts failure. There is no partial execution, fresh-noise retry or repair. Every predicted position remains constrained, while an unused-tail violation is reported separately and alone does not trigger the execution stop. §§6–7 distinguish pre-acceptance proposal violations, stops/numerical failures and successfully completed rollouts; stopping alone is not claimed as sampler improvement. Connecting arcs and physical tracking remain outside the guarantee.

`methodology_phase2.md` (lines 23–56, 64–85 and 95), `proposal.md` (lines 101–141 and 149), project `AGENTS.md` (lines 5 and 8–13) and project `README.md` (lines 19–27) agree with these operative choices and the continuing review hold. In the proposal, the initial actual-angle barrier at lines 109–118 is explicitly replaced by the internal angle for steering; it is not an alternative selected filter.

## Unresolved details are not new methodology blockers

The margin magnitude, activation/gain/cutoff, integration resolution, numerical near-zero limits, frame-initialization rule and measurable evaluation thresholds remain unselected. Phase 1 reproduction gaps also remain explicit. Those values are not needed to establish the analytic identities audited here, and this review selects none. Before any later approved implementation, they must become auditable operational choices; their eventual success remains an empirical question.

The approved method is therefore internally coherent as a limited feasibility study. This review neither strengthens its safety claims nor authorizes specifications, tickets, implementation or experiments. Applicant methodology review remains the current gate.
