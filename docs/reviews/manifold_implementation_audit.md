# Manifold-language audit against reference implementations

29 October 2026. Source-reading audit requested by the applicant. No project implementation, tests, simulation, installation, training or data preparation. Specification and tickets remain on hold. Review basis: `methodology.md` before this audit's geometry clarifications, at commit `aea0181`.

## Verdict

**The selected first-order product-sphere method is geometrically consistent. Its original mathematical presentation was too implicit about the metric, tangent-bundle/control interpretation and geometric diagnostics.** Ambient arrays and dot products are legitimate representations of the chosen geometry; sphere-valued outputs alone would not suffice. The clarifications below make the existing method intrinsic without adding physical dynamics, a different controller family or new numerical defaults.

This is source inspection of the geometric-CBF and official RFM implementations. Original-author RFMP LASA implementation remains unverified. SAD-Flower supplies the control-during-generation principle; a new fetch of its sampler failed in this audit, so no fresh source verification is claimed for it.

## 1. What the linked satellite code actually implements

The linked [satellite driver](https://github.com/mzdesa/Geometric_CBF/blob/main/satellite_sim.py#L12-L14) selects `SO3HalfSontag`; `SO3GradFlow` is the commented alternative. The script initializes attitude and angular velocity, not just a sphere point. [Raw script inspected](https://raw.githubusercontent.com/mzdesa/Geometric_CBF/main/satellite_sim.py).

[`Simulation/satellite.py`, `step`](https://github.com/mzdesa/Geometric_CBF/blob/main/Simulation/satellite.py#L42-L57) stores `(R,Omega)` and advances attitude through `R exp(dt*hat(Omega))`. Its plots use `q=R e3`, the projection to S². Thus a sphere plot must not be mistaken for the complete state. [Raw dynamics inspected](https://raw.githubusercontent.com/mzdesa/Geometric_CBF/main/Simulation/satellite.py).

[`SO3HalfSontag`](https://github.com/mzdesa/Geometric_CBF/blob/main/Control/so3_half_sontag.py) computes an inertia-scaled Riemannian gradient, a smooth safe configuration velocity, body-frame velocity error and a full-state barrier with a kinetic error term. It differentiates the safe field for backstepping and returns torque through the final filter. Its configuration barrier is **keep-in**, opposite our keep-out cone. These are geometry-dependent constructions, not generic dot-product formulas. [Raw controller inspected](https://raw.githubusercontent.com/mzdesa/Geometric_CBF/main/Control/so3_half_sontag.py).

The other [`SO3GradFlow` controller](https://github.com/mzdesa/Geometric_CBF/blob/main/Control/so3_grad_flow.py) also uses the mechanical metric and body-frame projected error. The two script options concern the safe velocity construction used inside the mechanical controller; they do not require every first-order manifold sampler to implement backstepping. [Raw controller inspected](https://raw.githubusercontent.com/mzdesa/Geometric_CBF/main/Control/so3_grad_flow.py).

Its final filter returns zero correction when the control Lie derivative is very small. Do not copy that fallback as a certificate for our unsafe-prior recovery: with a zero barrier gradient and a positive required recovery derivative, zero correction is infeasible. Our method's explicit failure branch is necessary; source inspection does not remove this distinction.

The more directly sphere-valued [`S2GradFlowCBF`](https://github.com/mzdesa/Geometric_CBF/blob/main/Control/sphere_grad_flow.py) still accepts `(q,v)`, scales the configuration gradient by inverse mass, subtracts a mass-weighted velocity-error term in its full-state barrier, and projects the final force into the tangent space. It is also second order. [Raw sphere controller inspected](https://raw.githubusercontent.com/mzdesa/Geometric_CBF/main/Control/sphere_grad_flow.py). The sphere simulation driver was read, but `Simulation/sphere.py` itself could not be fetched; its actual integrator is not verified here.

### Consequence for our study

Our configuration is the generated chunk `X`, not `(R,Omega)` or a physical `(q,v)` state. Our virtual control is an arbitrary tangent correction at `X`. The applicable geometric-CBF construction is the first-order bundle formulation, with input bundle `TM` and identity control action. We use its minimum-change filter; we do not claim to reproduce the satellite backstepping example. Its inertia metric, torque authority and derivative of a smooth safe velocity field are not inherited by our unit-sphere sampler. [Geometric CBF paper, §§III–V](https://arxiv.org/abs/2510.20202v1).

## 2. What actual RFM source confirms

The independent [RFM source audit](rfm_implementation_geometry.md) traces source symbols, revision and fetch limits. It verifies tangent projection of an ambient network, geodesic/JVP targets, metric regression and the distinction between projected Euler and exponential Euler. Generic RFM uses a uniform sphere prior; this does not resolve or replace RFMP's wrapped-Gaussian prior. Original RFMP settings still come from the paper.

Not every available RFM sampler configuration integrates intrinsically: flags select ambient integration, projection or exponential updates. Therefore “we use RFM code” would not by itself establish a geometry-preserving solver. A documented manifold update is required. [Official RFM solver](https://github.com/facebookresearch/riemannian-fm/blob/main/manifm/solvers.py), [pinned model/sampling source](https://github.com/facebookresearch/riemannian-fm/blob/b6ac1e9d60e18e594fb6310ec8a68d9ae683e2b2/manifm/model_pl.py).

## 3. Geometry that the methodology must state explicitly

For a chunk of `m` pointing directions, choose the product of unit round spheres:

```text
M = (S²)^m,
T_X M = product_i T_(x_i) S²,
g_X(V,W) = sum_i v_i^T w_i.
```

`M` has dimension `2m`; storing `3m` coordinates does not turn it into Euclidean space. Each tangent factor satisfies `x_i^T v_i=0`. For fixed generation time/context, the learned field is a section of `TM`; virtual controls belong to the same tangent fiber. There is no global identification of all tangent spaces with one fixed plane.

### Training and integration

State the source-to-data interpolation with the product exponential/logarithm, with both regression vectors based at the intermediate `X_s`. Under the declared round metric, the existing sum of ambient tangent dot products is exactly a Riemannian loss. No transport is needed when both vectors are already at that same point. [Official geodesic construction](https://github.com/facebookresearch/riemannian-fm/blob/main/manifm/manifolds/utils.py), [loss implementation](https://github.com/facebookresearch/riemannian-fm/blob/b6ac1e9d60e18e594fb6310ec8a68d9ae683e2b2/manifm/model_pl.py#L510).

A geometric Euler step must be identified as `Exp_X(ds*V)` or as a documented retraction. Normalized ambient Euler on each sphere is a retraction, not the exact exponential update; normalizing the complete concatenated chunk imposes the wrong constraint. Neither method certifies the barrier after a finite step. Step choice/resolution is still unresolved rather than borrowed from unverified RFMP code.

### Barrier and input bundle

For a scalar constraint `H_i(X)=h(x_i)`, write the intrinsic condition as

```text
dH_i|_X [V+U] = g_X(grad_g H_i, V+U) >= -phi(s) H_i,
minimize_U (1/2) g_X(U,U),       U in T_X M.
```

The existing `-(I-x_i x_i^T)c` is precisely the round-metric gradient in ambient coordinates; its other product factors are zero. Its dot pairing and the existing minimum-norm formula are therefore correct specializations. With a different metric or input distribution, one must derive the metric gradient/control adjoint again. Do not copy the satellite's inertia factor or interpret a tangent correction as torque.

The nonsmooth minimum-change law is appropriate for this first-order empirical formulation on its feasible domain; the smooth half-Sontag construction is important to the reference's differentiated backstepping law, which our scope excludes. Neither name nor closed form removes unsafe-center infeasibility or terminal numerical stiffness.

### Diagnostics

Use spherical distance for goal error, adjacent jumps and paired output displacement, and the product metric norm for interventions. Velocity comparisons at different points need transport to a common tangent space or an explicitly extrinsic label; raw subtraction is not an intrinsic acceleration. Adjoining positions can be compared through their distance without transporting them. These are interpretations of the already selected diagnostics, not an additional experimental study.

An ambient MLP projected to tangents is a valid geometric vector field, but does not automatically establish rotation equivariance. Likewise a wrapped Gaussian in a fixed tangent space is a valid prior construction, not a reason to learn the whole field in that one tangent plane. The repeated-point chunk prior is correlated and diagonal-supported; do not call it an independent product density or reuse full-dimensional likelihood code for it.

## 4. Disposition and remaining limits

The core method is retained. Clarifications incorporated into `methodology.md`: explicit `(M,g)`, `TM`/identity virtual actuation, source-to-data metric loss at a common base point, intrinsic CBF optimization, honest integration terminology and geometric interpretations of diagnostics. No numeric settings, library dependency or new physical controller is selected. Applicant review remains the current gate.

Geometric-CBF URLs above track mutable `main`, inspected on this date; an immutable revision was not obtained. The raw files were read successfully except the explicitly failed sphere-simulation fetch. Source code illustrates the authors' construction but was not executed or certified for correctness. No source availability or dependencies are inferred from a failed fetch, and no implementation permission follows from this audit.
