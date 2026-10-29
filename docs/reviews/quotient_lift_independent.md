# Independent mathematical review: proposed SO(3)/SO(2) lift

29 October 2026. Analytic review only. These formulas are a candidate representation, not an approved scope change. No implementation, specification, tickets, tests or numerical experiments were performed.

**Verdict:** the proposed signs, gradient, minimum-change filter and projected exponential-Euler update are correct under the stated round-metric, horizontal-lift hypotheses. They represent the existing first-order S² construction redundantly on SO(3). They do not supply a physical attitude controller, a globally defined roll convention, or an additional safety guarantee. The zero-gradient branches require explicit treatment.

## 1. Conventions and quotient geometry

Write `hat(u)w = u × w`, take unit `c`, `e3=(0,0,1)`, `0<theta_int<pi`, and set

```text
pi(R)=R e3=x,              Rdot=R hat(Omega),
H={Q in SO(3): Q e3=e3} ≅ SO(2).
```

The fibers are right cosets `R H`, so `SO(3)/SO(2) ≅ S²`. With

```text
g_R(R hat(u),R hat(v)) = u^T v
                     = (1/2) tr[(R hat(u))^T R hat(v)],
```

the vertical space is `R hat(span(e3))`; its metric-orthogonal horizontal complement consists of `Omega·e3=0`. Moreover

```text
d pi_R[R hat(Omega)] = R(Omega × e3),
|R(Omega × e3)|² = |Omega|² − (Omega·e3)².
```

Thus `pi` restricted to each horizontal space is an isometry onto `T_x S²` with its unit round metric. Its inverse is

```text
L_R(v)=R^T(x × v),                 v·x=0.
```

Indeed `L_R(v)·e3=0` and `(x×v)×x=v`. The factor `1/2` in the Frobenius metric matters: the unnormalized Frobenius metric gives body inner product `2u·v`, gradient body coordinates `b/2`, and a quotient metric twice the round metric. A consistent uniform rescaling of the optimization objective alone leaves its minimizer unchanged; mixing the gradient/norm conventions does not justify the displayed formulas.

## 2. Barrier differential, gradient and filter

Let

```text
h(R)=cos(theta_int) − c^T R e3,
b=−e3 × R^T c,
a=grad_S² h(x)=−(I−xx^T)c.
```

For every body direction `eta`, the scalar triple-product identity gives

```text
dh_R[R hat(eta)] = −(R^T c)·(eta×e3)
                 = (−e3×R^T c)·eta = b·eta.
```

Consequently `grad_SO(3) h = R hat(b)`, `hdot=b·Omega`, and `b=L_R(a)`. In particular `b·e3=0`, `|b|²=|a|²=1−(c·x)²`. The minus sign in the candidate is correct for the **outside-of-cap** safe set `h>=0`.

For `b!=0`, minimizing `(1/2)|Omega−Omega_nom|²` subject to `b·Omega>=−phi h` gives

```text
lambda = max(0, (−b·Omega_nom−phi h)/|b|²),
Omega_star = Omega_nom + lambda b.
```

The same solution results if horizontal admissibility is imposed explicitly, provided `Omega_nom=L_R(v_nom)`: both the nominal vector and correction are horizontal already. The isometry above implies

```text
b·Omega_nom = a·v_nom,
d pi_R[R hat(Omega_star)] = v_nom + lambda a = v_star.
```

This is exactly the round-metric S² minimum-change tangent filter, with the same multiplier and intervention norm. All statements extend factorwise to the product `(SO(3)/SO(2))^m ≅ (S²)^m`, with the sum metric; coupling in the learned nominal field does not invalidate this pointwise calculation.

This specialization agrees with the general bundle CBF-QP construction using the metric gradient and control adjoint in [de Sa, Ong and Ames, Section III-C](https://arxiv.org/html/2510.20202v1#S3.SS3). The paper's mechanical backstepping and inertia-metric satellite construction are separate results and are not consequences of this first-order lift.

## 3. Continuous and finite-step equivalence

Along a solution of the horizontal lifted ODE, projection gives exactly `xdot=v_star(s,x,context)` by the chain rule. Conversely, a differentiable S² path and an initial frame over its starting point determine a horizontal lift through this ODE. This assumes the nominal field depends on the directions/context, rather than on arbitrary frame axes. The lift does not require the learned field to be equivariant under spatial rotations.

For one frozen-vector step, let `q=|Omega_star|=|v_star|`. Since `Omega_star·e3=0`, Rodrigues' formula gives exactly

```text
R_next = R exp(ds hat(Omega_star)),
R_next e3 = cos(ds q)x + [sin(ds q)/q] v_star
          = Exp_x(ds v_star),
```

with the `q=0` value understood by continuity. Hence projected iterates agree in exact arithmetic when fields, inputs and time grids agree. This identity is valid even past the injectivity radius; it does not assert uniqueness of the shortest geodesic there. It identifies exponential Euler, not normalized ambient Euler. Neither representation makes a finite step the exact solution of the state/time-varying filtered ODE or ensures that the barrier remains satisfied across or after that step.

Adding an arbitrary vertical spin `zeta e3` preserves the **instantaneous** projected velocity, but in general changes `R exp(ds hat(Omega+zeta e3))e3`. Therefore horizontality is essential to this finite-step equivalence. The candidate correctly enforces it.

## 4. Gauge covariance and the meaning of zero spin

For a constant gauge change `R'=RQ`, `Q e3=e3`, the same direction has

```text
b'=Q^T b,      Omega_nom'=Q^T Omega_nom,
lambda'=lambda, Omega_star'=Q^T Omega_star.
```

Cross products commute with rotations, and all the scalar products are invariant. Also

```text
R' exp(ds hat(Omega_star'))
  = R exp(ds hat(Omega_star)) Q.
```

Thus arbitrary initial roll does not change the generated directions. A time-dependent frame relabeling is different: if `Q(s)` has `Q^T Qdot=hat(kappa e3)`, then its body velocity is `Omega'=Q^T Omega+kappa e3`. The extra vertical term is required. Horizontal lifting chooses a connection and is covariant under constant fiber rotations; it is not a promise that every time-dependent roll convention remains horizontal.

Zero spin means `Omega·e3=0` instantaneously. For `r1=R e1`, `r2=R e2`, their derivatives are normal to the sphere, so `P_x r1dot=P_x r2dot=0`: these tangent frame vectors undergo round-sphere parallel transport. Parallel transport can return rotated after a closed loop. An analytic example is the geodesic triangle `e3 → e1 → e2 → e3`. Successive horizontal great-circle transports take the initial tangent vector `e1` to `−e3`, then `−e3`, then `e2`; the direction returns to `e3` while the frame has acquired a quarter-turn. No numerical experiment is involved in this example. Consequently “no instantaneous spin” does not imply globally zero roll or path-independent frame recovery.

There is no global continuous section `R(x)` with `R(x)e3=x`: its first column would be a continuous nowhere-zero tangent unit field `R(x)e1` on S², contradicting the hairy-ball theorem. The needed theorem is stated in [Francis Su's author-maintained mathematical notes](https://math.hmc.edu/funfacts/hairy-ball-theorem/). Local frame sections, patches with SO(2) transition functions, or a frame carried along each path are mathematically valid. A pointwise minimal rotation from `e3` to `x` has an unavoidable branch at `x=−e3`; a single globally smooth roll prescription cannot remove the obstruction. Carrying a valid initial frame avoids demanding such a global section, while retaining path dependence.

## 5. Pole branches, recovery and metric changes

**Barrier degeneracy is separate from frame-chart singularity.** Here `b=0` exactly when `x=±c`, regardless of frame choice. At `x=c`, `h=cos(theta_int)−1<0`, so the constraint `0>=−phi h` is infeasible when `phi>0`. No first-order angular correction changes that instantaneous differential. At `x=−c`, `h=cos(theta_int)+1>0`; zero correction is feasible for `phi>=0`. If `phi=0`, the differential constraint is also feasible at the unsafe center but does not give recovery. Dividing by a clipped denominator cannot fix the infeasible positive-gain center branch. Near `x=c` the denominator is small and the lift preserves, rather than cures, the S² filter's ill-conditioning.

The quotient representation also preserves all existing recovery limitations: an unsafe initial condition is not made forward invariant by a CBF inequality; a singular terminal gain is not a finite-step certificate; an internal cone margin gives no numerical residual bound by itself; and safe generated waypoints do not certify their connecting arcs.

For a different body metric `g_J(R hat(u),R hat(v))=u^T Jv`, with symmetric positive definite `J`, the corresponding full-space formulas instead are

```text
grad_J h = R hat(J^−1 b),
Omega_star = Omega_nom
  + max(0,(−b·Omega_nom−phi h)/(b^T J^−1 b)) J^−1 b.
```

These follow directly from the gradient definition and the weighted quadratic objective. For generic `J`, `J^−1b` can have vertical spin and need not project parallel to the round-sphere gradient. Metric horizontality is now `Omega^T J e3=0`, which need not be the candidate's `Omega·e3=0`. A fixed-body metric is invariant under the right SO(2) gauge action precisely when `QJQ^T=J` for every such `Q`, namely `J=diag(alpha,alpha,beta)` in this basis. That axisymmetric but possibly non-isotropic case retains the horizontal plane; its quotient metric is `alpha` times the round metric and the scalar factors cancel in this unbounded single-constraint filter. Generic anisotropy lacks this gauge-independent round quotient interpretation. A physical inertia metric therefore cannot be silently substituted, even though its entries are also represented by arrays and dot products.

**Review conclusion:** the candidate is a correct horizontal, normalized-metric quotient lift of the existing S² sampler and filter. Describing it as a representational equivalence is justified. Describing it as a unique attitude reconstruction, global zero-roll model, mechanical-controller reproduction or stronger safety result is not justified. Adoption remains the applicant's decision.
