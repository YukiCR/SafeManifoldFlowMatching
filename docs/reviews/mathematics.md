# Independent mathematical methodology review

29 October 2026. Reviewed `methodology.md` at commit `c300c67`, lines 1–154, against the supplied SAD-Flower and geometric-CBF papers and the original RFM paper. This is an advisory review, not approval of implementation or of numerical settings. No code, tests, data preparation or experiments were performed.

**Verdict: qualified mathematical pass for the stated empirical study.** The sphere gradient, constraint sign, minimum-change correction, product-space separation and execution acceptance logic are correct. I found no mathematical blocker requiring a different formulation. The method does **not** establish recovery for every prior sample, a discrete numerical safety theorem or useful obstacle detours. Its practicality depends on finite-budget failure handling and a credible learned baseline; an informative negative result remains possible within the approved scope.

## Verified derivation

For unit `x,c`, `h=cos(theta_int)-cᵀx` is nonnegative outside the internal cap. Projecting its ambient gradient gives `a=-(I-xxᵀ)c`, with `xᵀa=0` and `||a||²=1-(cᵀx)²`. Thus positive motion along `a` increases clearance. The sign in lines 87–95 is correct.

Write `b=aᵀV+phi*h`. If `b>=0`, `U=0` is optimal. Otherwise Cauchy–Schwarz gives `||U||>=-b/||a||`; equality is attained uniquely by `U=(-b/||a||²)a`. This verifies lines 101–114, including tangency. It is the single-integrator specialization of geometric CBFs, §III.C, Proposition 1, Eqs. (9)–(17); that proposition's CBF/domain assumptions must not be extended to the infeasible unsafe center. Because the objective is a sum and each constraint involves only one `U_i`, the minimization separates even when the nominal network couples the chunk. Adding adjacent-position constraints or correction bounds would change this conclusion.

Phase 1's tangent regression, product metric and correctly directed source-to-data geodesics (line 56) agree with RFM §3.1, Eq. (10), and §3.2, Proposition 3.2/Eq. (15), away from the sphere cut locus. Coincident/antipodal handling remains an appropriate later numerical choice. This does not independently verify RFMP's inherited hyperparameters.

## Findings and smallest remedies

| Severity and status | Affected methodology | Finding, impact and smallest remedy |
| --- | --- | --- |
| **Medium; practical risk, not an omitted algebraic case** | §5, lines 108–122 | Near-center conditioning is more serious than exact-center infeasibility. At angular distance `r` from `c`, `||a||=sin(r)` and, for bounded nominal `V` and positive finite `phi`, active `||U||` grows approximately as `phi*(1-cos(theta_int))/r`. The unsafe untruncated prior permits such candidates; a cap near the prior's north-pole center can make near-center samples relevant. Add this conditioning warning. Later numerical rules must detect and count a failed solve when its finite budget cannot handle it; denominator clipping or silently bounding `U` does not preserve the stated inequality. No safe-prior substitution is needed or recommended here. |
| **Medium; design limitation already partly acknowledged** | §5, lines 118–122; §7, lines 138–142 | The singular schedule is not a finite-step recovery certificate. SAD-Flower §5.2 and Appendix B.3 state stronger positivity claims, but the equality solution admitted by the same inequality can remain negative for every `s<1`. The methodology correctly resists inheriting that claim. Any terminal-limit argument additionally needs existence to the endpoint and a continuous limiting state. Keep terminal recovery an objective, not an unconditional theorem; explicitly require `gamma>0`. The optional bound below can explain why the internal margin helps before the singular endpoint. |
| **Medium; intrinsic method limitation, not a blocker** | §5, lines 101–114; §7, lines 136–142 | Minimum change supplies barrier-normal motion only. On the internal boundary, an inward nominal field can be canceled without creating tangential progress; if it has no useful tangential component, the candidate stalls. A jointly learned field can also be evaluated far from its training support after steering. Safety steering therefore need not discover a detour or preserve useful motion. Keep stalls, completion, roughness and goal error as coequal outcomes. No new guidance objective is necessary for this study, and adding one would be a separate design decision. |
| **Low; retain the existing distinction** | §6, lines 126–132; §7, lines 136–142 | Checking the entire execution portion before advancing gives discrete accepted-waypoint safety when geometry and the check are valid and the supplied initial direction is safe. It gives neither all-chunk success nor safety of connecting arcs. A safe accepted prefix with an unsafe unused tail is simultaneously an execution acceptance and a whole-chunk failure. Preserve these separate labels and report both denominators; the current text already does so correctly. |

## Analytic margin interpretation

The following is my deduction, not a theorem transferred from either safety paper. Let `Delta=cos(theta)-cos(theta_int)>0`, `B=1-cos(theta_int)`, and `Phi(s)=integral_(s_on)^s phi(r) dr`. If a feasible exact solution satisfies the differential inequality throughout a finite interval, the integrating-factor comparison gives

```text
h_internal(s) >= h_internal(s_on)*exp(-Phi(s))
              >= -B*exp(-Phi(s)),
h_actual(s)   >= Delta-B*exp(-Phi(s)).
```

Consequently `Phi(s*)>=log(B/Delta)` is a conservative sufficient condition for actual-cap recovery at a finite `s*<1` in that ideal system. For the proposed schedule, `Phi(s*)=gamma*(1/(1-s*)-1/(1-s_on))`. This shows how a positive internal margin can permit actual safety while the internal barrier remains negative. It does not bound integration or inequality residual errors, solve center infeasibility, or show that stopping the learned generator early preserves its endpoint distribution. Lines 97 and 138 correctly require a direct final check and a matched unsteered numerical protocol.

SAD-Flower §5.3/Theorem 5.1 assumes QP feasibility. Its Appendix B.1 feasibility argument uses independent differentiable signed-distance constraints with unit gradient. The smooth spherical dot-product barrier here has zero gradients at `±c`, so that particular argument cannot simply be imported. The exact unsafe center is infeasible; the antipodal safe point admits zero correction. Geometric CBFs' Proposition 1 likewise relies on its feasible CBF domain. The methodology's explicit branches and restricted claims are therefore essential.

## Blockers versus later choices; practicality

**Methodology blockers: none found under the present empirical claims and explicit failure allowance.** A requirement to recover every source sample or guarantee every returned chunk would be blocked by the present formulation; neither is currently claimed.

**Later numerical decisions:** margin/gain/activation, finite terminal time and grid, tolerances, near-zero-gradient handling, finite computation limits and failure labels. These are necessary before implementation, but this review selects no values or new algorithm. Pointwise constraint satisfaction during continuous generation does not survive a numerical update automatically, even when the exponential update preserves sphere membership.

The closed-form one-cap filter is inexpensive relative to network evaluation and avoids a QP dependency. The principal mathematical implementation risk is the combination of center ill-conditioning and terminal stiffness; the larger project risk is obtaining a validated RFMP baseline within the remaining budget. The proposed paired comparisons and failure accounting can yield a useful, honest study without proving universal safety or adding a navigation planner.

Primary sources: [geometric CBFs, §III.C, Proposition 1](https://arxiv.org/abs/2510.20202v1); [SAD-Flower, §§5.1–5.3 and Appendix B.1/B.3](https://arxiv.org/html/2511.05355v3); [RFM, §§3.1–3.2](https://arxiv.org/html/2302.03660v3). The two safety sources were checked using the supplied local paper extracts.
