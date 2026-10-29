# Manifold safety references for the proposed flow-matching project

Research checked 29 October 2026. This is a design note, not implementation approval. No code, training, simulation or benchmark from these references was executed. The supplied local PDFs were read via extracted text, including the safety constructions and relevant theory/experiment appendices.

## Main conclusions for the proposal

1. A tangent-velocity controller on `S²` with a forbidden spherical cap is a defensible small experiment linking learned policies, geometry and safety. It is a first-order kinematic pointing problem. It does not establish torque-level satellite control or deformable-object manipulation.
2. A geometric CBF filter can preserve a safe set under its assumptions. It does not automatically preserve convergence of a nominal learned flow. Deadlock and target-reaching must be treated as separate outcomes.
3. SAD-Flower operates on a whole state/action trajectory in **generation time**, whereas the proposed pointwise sphere controller would act in **physical execution time**. Reusing its control-augmentation idea is reasonable; calling the sphere controller a reproduction of SAD-Flower is inaccurate.
4. No benchmark-scale dataset or MuJoCo deployment is needed for the sphere experiment. A compact, explicitly described synthetic demonstration source is more compatible with 18 hours. Dataset generation itself remains an implementation/experiment step requiring approval.

## 1. SAD-Flower

**Source supplied by applicant:** Huang et al., *SAD-Flower: Flow Matching for Safe, Admissible, and Dynamically Consistent Planning*, arXiv:2511.05355v3, 7 June 2026, 24 pages. The local PDF header matches the current v3 metadata. [Paper](https://arxiv.org/abs/2511.05355v3).

### Endpoint conditions: additional source check

Remark 4.1 explicitly conditions the initial trajectory state and holds its generation derivative at zero. Appendix F's Maze2d paragraph additionally states that the model is conditioned on both start and goal. These are task-dependent choices; the generic formulation and locomotion experiments should not be described as universally pinning a goal. [Remark 4.1](https://arxiv.org/html/2511.05355v3#S4), [Appendix F](https://arxiv.org/html/2511.05355v3#A6).

The author repository's `apply_conditioning` assigns the supplied state values at specified horizon indices. `ConditionedODESolver` and `CBFCLFODESolver.ode_func` zero the derivatives at conditioned indices, including after adding guidance, so supplied conditions stay fixed during generation. [Helper definition](https://github.com/TzuYuan107/sad-flower/blob/main/gflower/models_flow/flow_matcher.py), [ODE solver source](https://github.com/TzuYuan107/sad-flower/blob/main/gflower/models_flow/flow_policy.py). These files were inspected read-only; no code was executed.

For the proposed LShape planning task, fixing start/goal is therefore aligned with the Maze2d-style boundary-conditioned construction. RFMP's observation-conditioned action chunks are different: Section IV-A/Algorithm 1 generates a horizon from a prior and executes its first actions, without specifying this same pair of clamped endpoints. [RFMP Section IV-A](https://arxiv.org/html/2412.10855v3#S4.SS1). The recommendation does not itself constitute applicant approval of the endpoint design.

### What its controlled system is

Sections 3–5 distinguish two indices. A physical plan is `τ = {(s(k), a(k))}_{k=0}^{H-1}` with dynamics `s(k+1)=f(s(k),a(k))`. The generative ODE evolves the **entire** plan in flow time `t∈[0,1]`:

```text
dτ_t/dt = v_theta(t, τ_t) + u_t.
```

Here `u_t` is a virtual correction to the generative vector field, not a force/torque delivered directly to the robot. Initial-state coordinates of the plan are fixed during generation. State and action constraints apply to every discrete physical index `k` of the final generated plan.

The method leaves the first generation interval `[0,T0)` uncontrolled, then solves a minimum-norm correction QP. State/action CBF inequalities have the form `dh_k/dt ≥ -φ(t) h_k`. Its CLF is

```text
V(τ) = 1/2 Σ_k ||s(k) - f(s(k-1), a(k-1))||²,
dV/dt ≤ -φ(t) V,
φ(t) = c/(1-t)².
```

**The CLF concerns consistency with dynamics. It is not a goal-distance CLF.** Desired behavior comes from conditioning and learned trajectory data.

### Guarantees and qualifications

Theorem 5.1 assumes the joint QP remains feasible over the controlled generation interval and concludes constraint satisfaction at generation terminal time `t=1`. Appendix B discusses individual CBF/CLF feasibility, then explicitly acknowledges that coupling them can cause infeasibility. Separate individual feasibility does not prove feasibility of their intersection.

The singular prescribed-time gain must be distinguished from a finite-precision implementation. As a mathematical check of the proposed reuse, the equality solution `h(t)=h(T0) exp(-∫φ)` remains negative for every `t<1` when `h(T0)<0`; it tends to zero from below. Therefore, this mechanism is not a claim that an initially unsafe *generation path* is safe throughout. For a physical sphere trajectory that must be safe from the start, initialize inside the safe set and enforce its barrier from the first execution step.

Appendix B.4 treats learned dynamics error using a uniform error bound and Lipschitz propagation. Such bounds and a robust design are additional assumptions; learning a forward model does not supply them automatically. Adding norm-dependent robustness terms changes the QP to an SOCP. Appendix J states physical-robot deployment remains future work, with model uncertainty, sensing and computation still relevant.

Experiments include D4RL Maze2d, Hopper and Walker2d and PyBullet Kuka block stacking; additional Adroit results examine higher-dimensional manipulation. Kuka is specifically a **state-constraint-only** variant, without action/dynamic-consistency enforcement. Do not interpret every experiment as validating all three mechanisms. The main text and appendix also give different numerical Maze action-bound descriptions, so an exact reproduction would need to resolve configuration values rather than copy one sentence.

### Resources actually checked

- A public author-named repository exists at [TzuYuan107/sad-flower](https://github.com/TzuYuan107/sad-flower). Its README identifies this paper and GitHub reports an MIT license. It describes Docker/MuJoCo setup and separate flow, value and dynamics training plus Maze2d evaluation scripts. This is appreciably more setup than a sphere-only experiment needs.
- The tree exposes `gflower/CBFCLF_tool`, models, datasets, environments and sampling directories. The inspected [CBF/CLF generator source](https://github.com/TzuYuan107/sad-flower/blob/main/gflower/CBFCLF_tool/CBF_CLF_generator.py) imports PyTorch, `qpth` and `functorch`; it constructs constraint/Jacobian machinery over horizon coordinates. This confirms a substantial trajectory-space implementation, rather than a ready-made manifold controller.
- No pretrained-checkpoint download link was identified in the README inspected. This is an availability limitation of this check, not proof that no checkpoints exist.
- The paper's project URL [sadflowerplanning.github.io](https://sadflowerplanning.github.io/) returned HTTP 404 via the browsing tool. The repository is accessible, so do not depend on the demo site.
- Full environment-file/raw-file fetches were unavailable through the browsing tool; shell network reads were restricted. No dependency installation or dataset download was attempted.

**Reuse recommendation (our inference):** borrow the controlled-generative-flow perspective and explicit constraint accounting. For the deadline, derive and test a small tangent-space filter rather than import its complete MuJoCo/D4RL training pipeline.

## 2. From Bundles to Backstepping

**Source supplied by applicant:** de Sa, Ong and Ames, *From Bundles to Backstepping: Geometric Control Barrier Functions for Safety-Critical Control on Manifolds*, arXiv:2510.20202v1, 23 October 2025, 8 pages. [Paper](https://arxiv.org/abs/2510.20202v1).

### The geometric CBF and filter

Section III poses a control system on an input bundle over a manifold. Safety means forward invariance of `C={p:h(p)≥0}`. Theorem 1 uses a regular boundary with an inward-pointing vector field or a barrier inequality on a neighborhood. Controllers need sufficient regularity for their flows to be well-defined.

For a control-affine system with state/input metrics, Proposition 1 gives the minimum-norm correction:

```text
kappa_safe = kappa_nom + max(0, -a/b) G* grad h,
a = alpha(h) + <grad h, f + G kappa_nom>,
b = ||G* grad h||²,
```

with a separate `b=0` branch. Corollary 1 establishes local Lipschitz regularity and invariance under the stated CBF assumptions. Smooth safety filters are developed because later backstepping differentiates the safe velocity field. A nonsmooth minimum-norm filter should not casually be substituted into a construction that requires smoothness.

### Why the backstepping part matters

Section IV considers simple mechanical systems on configuration manifold `Q`, whose full state is a tangent vector in `TQ`. A configuration-only constraint generally has relative degree two under force control. The construction first finds a smooth safe velocity field `κ(q)`, then forms

```text
h(v_q) = h0(q) - epsilon/2 ||(v_q - kappa(q))_A||².
```

The kinetic-energy metric defines the norm, and `_A` is projection to actuated directions. Theorem 2 requires unactuated directions to lie in `ker dh0`; this is automatic only in the fully actuated case. Proposition 2 needs an initial full state satisfying `h(v_q(0))≥0`. Merely starting at a safe configuration `h0(q(0))≥0` does not certify an arbitrary incoming velocity.

The example is an underactuated rigid body on `SO(3)` with symmetric inertias and torque authority about two body axes. Its actual constraint is

```text
h0(R) = e3ᵀ R e3 - cos(theta_safe) >= 0,
```

so the heat-shield direction must stay **inside** a safe angular cone. The `S²` plot is the projection `R↦Re3`. The user's proposed forbidden cone reverses the inequality; it should be derived independently, not copied with the original sign.

### Resources actually checked

The first author's [GitHub repository listing](https://github.com/mzdesa?tab=repositories) exposes [mzdesa/Geometric_CBF](https://github.com/mzdesa/Geometric_CBF), described as “Geometric CBF Controllers.” Its tree includes `sphere_sim.py`, `satellite_sim.py`, and `Control/`, `Simulation/`, `Plots/`. This is a relevant author-owned implementation resource, although the inspected paper does not explicitly designate that URL as its official reproduction package.

The root listing did not display a README or license. Source-file/raw-file fetches failed in the browsing tool, so dependency versions, exact implementation fidelity, and reuse permission have not been verified. No code was cloned, installed or run. Use it as a read-only reference until license and source details can be inspected.

## 3. Our specialization to the proposed sphere experiment

These equations are our derivation from the geometric CBF setup, not a statement that either paper implements this learned sphere policy.

Let `x∈S²`, forbidden direction `c∈S²`, and exclusion half-angle `theta∈(0,pi)`. Require `angle(x,c)≥theta`. Define

```text
h(x) = cos(theta) - cᵀx,
P_x = I - xxᵀ,
a(x) = grad_S² h(x) = -P_x c.
```

For a kinematic control `xdot=v∈T_xS²`, constrain `aᵀv≥-gamma h`. With tangent nominal velocity `v_nom`, a single-cap, unbounded-velocity minimum-norm filter has

```text
v_safe = v_nom + max(0, -(aᵀv_nom + gamma h)/||a||²) a.
```

The nonzero-gradient formula needs a well-defined zero-gradient branch. At the boundary `||a||²=sin²(theta)>0`; at the antipode of the cap center the state is safely interior and the barrier inequality is inactive. Starting at the forbidden center cannot be justified by ordinary forward-invariance theory. Goals must have strict clearance and starts must satisfy the safe-initialization condition.

The correction is tangent because both `v_nom` and `grad_S² h` are tangent. A geometry-preserving integrator can enforce sphere membership. That alone does not establish forbidden-cap avoidance between finite steps: retraction/normalization fixes the norm constraint, not obstacle clearance. Check the exact great-circle arc or sufficiently conservative intersample condition and report step-size sensitivity.

For multiple caps, `v=0` remains feasible at any safe state for the pure kinematic CBF inequalities, provided the input set includes zero. Adding a hard progress CLF can destroy feasibility. A soft progress objective can preserve safety while losing progress; report that fact instead of hiding stalled trajectories.

## 4. Scope and evidence recommendation within 18 hours

Recommended core: one fixed safe goal, one spherical cap, demonstrated nontrivial detours, genuinely learned tangent flow, CBF filtering in explicitly chosen execution time, and an unfiltered comparison. Retain an intentionally symmetric start/obstacle/goal case to expose possible deadlock. A second cap, acceleration/torque dynamics, unknown perception and physical deployment are extensions, not core promises.

Record minimum clearance, barrier residual, sphere norm error, target error/reaching rate, speed, intervention size, integration resolution, and failed/stalled trajectories. Distinguish mathematical continuous-time invariance under the kinematic model from measured finite-step behavior. Convergence of the filtered policy needs its own argument or bounded empirical claim; it is not inherited from the stable nominal-flow paper.

An honest project statement after completion could concern learning and filtering a manifold-valued kinematic policy and evaluating the safety–progress tradeoff. It should not claim full rigid-body dynamic consistency, global target convergence, realistic deformable manipulation, or a new theoretical guarantee unless those have actually been established.

## Addendum: the user requires filtering the FM generation dynamics

The applicant clarified that the primary design must correct the generative FM dynamics, rather than place a safety filter downstream on a trajectory-following controller. Two distinct sampler states can implement that intention. The following compares them without choosing on the applicant's behalf or authorizing implementation.

### A. A single sphere point evolves during generation

Let `s` denote generation time and sample `x(0)` from a safe base distribution. The learned sampler evolves

```text
dx/ds = v_theta(s,x;goal) + u(s,x),
v_theta, u ∈ T_xS².
```

Here the *entire generated curve* `s↦x(s)` is retained as the planned pointing path. The CBF acts directly during FM generation. This satisfies the clarification: there is no downstream tracking filter in the core construction.

For the cap barrier above, choose the minimum-norm tangent correction with

```text
<grad h, v_theta + u> >= -gamma h.
```

If generation starts in `C`, the total generator is sufficiently regular, and the inequality holds continuously, the **generation trace** remains in `C`. This is a direct manifold-CBF invariance argument. Filtering must start at `s=0` if all of that trace is part of the desired safe path; SAD-Flower's delayed activation should not be copied blindly.

With unbounded tangent virtual correction, feasibility is simple at a safe state: `u=-v_theta` makes the total velocity zero, satisfying the inequality. **Zero correction `u=0` is not the same as zero total velocity** and need not be safe. A bound on correction magnitude can invalidate that cancellation; a bound on total tangent speed that includes zero does not create the same problem.

If the robot later follows the path by a positive monotone retiming `x_robot(t)=x(s(t))`, the geometric forbidden-direction property is retained, provided execution exactly follows that curve. The speed rescales by `ds/dt`. This is a geometric path statement, not a torque/acceleration guarantee or robustness to tracking error. If numerical sampling yields great-circle segments, certify/check their clearance as well as node clearance; preserving the sphere norm alone is insufficient.

This design is **inspired by control-augmented FM**, but it generates one geometric path from a point sampler. SAD-Flower instead transports a distribution over whole state/action trajectories. It should be presented as a small manifold-flow adaptation, not an implementation of all SAD-Flower guarantees.

One modeling decision must be explicit: if `x(0)` is a random safe orientation, each generated path starts there. A fixed known robot start is a different conditioning problem. A deterministic ODE from one fixed start yields one trace for a fixed goal/model; multimodal paths require additional sampled conditioning or another stochastic variable. Also, truncating a previously learned uniform-sphere base distribution to a new safe set changes the prior; combined with filtering, it changes the generated distribution. Do not claim the original density is preserved exactly.

### B. A full trajectory evolves on a product manifold

Let `X(s)=(x_0(s),…,x_{H-1}(s))∈(S²)^H`, with whole-path generation dynamics `dX/ds=V_theta(s,X)+U(s,X)`. Each coordinate is tangent to its own sphere. Fix start and goal by pinning `x_0` and `x_{H-1}` throughout generation; their total generator components must be zero, not merely their corrections.

Per-waypoint barriers `h_i(X)=cos(theta)-cᵀx_i` constrain **every waypoint in the generated final plan**. If all waypoints of `X(0)` are safe and CBF inequalities apply from `s=0`, all waypoints also remain safe at every generation time. If the initial whole trajectory is unsafe and a prescribed-time recovery mechanism is used, only a terminal-generation constraint claim may be appropriate.

Neither claim ensures that the interpolated physical path is safe between adjacent waypoints. Two safe sphere points can have a shortest great-circle segment that cuts through the cap. A whole-path constraint must account for each segment, for example

```text
b_i(X) = cos(theta)
         - max_{r∈[0,1]} cᵀ Slerp(x_i,x_{i+1};r) >= 0.
```

This maximum introduces differentiability issues, and antipodal pairs make shortest-arc interpolation nonunique. Smooth conservative segment constraints or explicitly checked segments require additional design. A safe initial trajectory must satisfy these path constraints, not only safe waypoint sampling. Constructing it is an additional dependency that can already require a geometric planner or carefully designed demonstration path.

For a safe full path and unbounded tangent virtual correction, cancellation of the nominal generator again gives zero total velocity and makes ordinary CBF inequalities feasible, including endpoint pinning. This does not imply progress toward the learned target trajectory. If hard terminal/progress CLFs are added, joint feasibility needs its own analysis. With unsafe source trajectories, the same cancellation cannot establish recovery: it merely freezes an unsafe path.

This formulation is structurally closer to SAD-Flower's whole-trajectory generator. It still differs by using a product of spheres, and it has no state/action dynamic-consistency guarantee unless physical actions and a transition model are included explicitly. Calling sphere membership “dynamic consistency” would conflate a configuration constraint with equations of motion.

### A concrete deadlock in the single-point generator

This analytic counterexample is a design calculation, not an experiment. Let the forbidden center be `c=(0,0,1)` and cap radius `theta=pi/6`. Choose the safe boundary start and safely interior goal

```text
x = (1/2, 0, sqrt(3)/2),
g = (-sqrt(3)/2, 0, 1/2).
```

The goal has clearance `h(g)=sqrt(3)/2-1/2>0`. The nominal goal-seeking tangent field `v_nom=P_x g` equals `g`, because `xᵀg=0`. At the boundary,

```text
a = grad h(x) = (sqrt(3)/4, 0, -1/4),
v_nom = -2a,
h(x)=0.
```

The CBF requires `aᵀv_safe≥0`. Minimum-norm projection removes the entire nominal vector, giving `v_safe=0`. Thus the filtered generator remains safe but never reaches a feasible goal. A geodesic-log goal field is a positive scalar multiple of this vector and has the same failure. Starts slightly outside this boundary approach it without resolving the meridional symmetry.

This shows why adding an output-stabilizing nominal flow does not by itself prove convergence after CBF augmentation. A tangential detour mechanism, a navigation construction, or route conditioning can resolve selected cases, but each is a separate design decision. Record stalled runs rather than exclude them. Under the 18-hour cap, formulation A has fewer coupled constraints and dependencies; formulation B offers a closer SAD-Flower analogy at greater implementation and validation cost. The applicant must choose this tradeoff before specification and tickets.
