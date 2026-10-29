# RFM implementation geometry audit

29 October 2026. Source-reading audit of `methodology.md`; no implementation, tests, data preparation or experiments. Recommendations below do not change approved project decisions.

**Finding:** the method already has the essential manifold structure. Its use of three-dimensional coordinates, dot products and an ambient MLP is compatible with intrinsic sphere geometry. The useful correction is to state the product tangent space and metric explicitly, then use that interpretation consistently in training, steering and evaluation. Introducing coordinate charts or parallel transport everywhere would add work without fixing a demonstrated problem.

## Verified implementation evidence

This audit inspected actual files in Meta's official `facebookresearch/riemannian-fm`, rather than treating a paper or README as implementation evidence. GitHub's [commit history](https://github.com/facebookresearch/riemannian-fm/commits/main/) identifies revision [`b6ac1e9d60e18e594fb6310ec8a68d9ae683e2b2`](https://github.com/facebookresearch/riemannian-fm/commit/b6ac1e9d60e18e594fb6310ec8a68d9ae683e2b2). The pinned `model_pl.py` was fetched successfully. Other RFM files cited below were read at mutable `main`, accessed on this audit date; their pinned raw URLs did not all resolve through the browsing tool, so their exact content at that revision is **not independently verified** here.

| Source and symbols | Verified behavior | Consequence for our method |
| --- | --- | --- |
| [`manifm/manifolds/sphere.py`: `Sphere`, `random_base`, `base_logprob`, `transp`](https://github.com/facebookresearch/riemannian-fm/blob/main/manifm/manifolds/sphere.py) | Inherits Geoopt's sphere operations; selects the uniform sphere base and constant surface-density log probability; overrides transport with a closed-form expression and a near-antipodal fallback. | Official RFM's base is **uniform**, not RFMP's wrapped Gaussian. A transport method's existence does not make it necessary in every loss/update. |
| [`manifm/model/arch.py`: `ProjectToTangent.forward`, `tMLP`](https://github.com/facebookresearch/riemannian-fm/blob/main/manifm/model/arch.py) | For the sphere branch, projects the input point, evaluates an ambient network, then calls `proju` at that point. | Ambient inputs/outputs do not imply Euclidean dynamics. The actual field is a tangent vector field. |
| [`manifm/manifolds/utils.py`: `geodesic`](https://github.com/facebookresearch/riemannian-fm/blob/main/manifm/manifolds/utils.py) | Computes a shooting tangent by `logmap(start,end)`, scales it by time, then applies `expmap` at the start. | State the direction as source to data; this is not linear interpolation followed by normalization. |
| [`manifm/model_pl.py`: `rfm_loss_fn`](https://github.com/facebookresearch/riemannian-fm/blob/b6ac1e9d60e18e594fb6310ec8a68d9ae683e2b2/manifm/model_pl.py#L510) | The ordinary sphere branch differentiates that geodesic by `jvp`, vectorizes over examples, subtracts the target from the predicted field at the same intermediate point, and applies `manifold.inner(...).mean()/self.dim`. | This is a metric loss on a common tangent space. The code's normalization is by its stored representation dimension; do not silently identify it with intrinsic dimension. |
| [`manifm/solvers.py`: `euler_step`, `projx_integrator`, `midpoint_step`](https://github.com/facebookresearch/riemannian-fm/blob/main/manifm/solvers.py) | Euler uses `expmap(x,dt*v)` when passed a manifold; otherwise it adds `dt*v` in ambient space. The integration loop independently controls point projection. The manifold midpoint branch transports its intermediate field before the final exponential step. | Distinguish exponential Euler from projected ambient Euler. Transport is relevant when a solver combines vectors based at different points. |

`ManifoldFMLitModule.sample` reads `local_coords=False` and `eval_projx=False` as configuration defaults. With both false it uses adaptive ambient `odeint`; otherwise it uses Euler on a 1001-point unit-interval grid, forwarding those flags. `sample_all` uses that grid with `projx=True` and omitted/default-false `local_coords`. Its likelihood calculation constructs a product with a Euclidean log-density accumulator; that is not RFMP action-chunk code. [Pinned `model_pl.py`, `sample`, `sample_all`, `compute_exact_loglikelihood`](https://github.com/facebookresearch/riemannian-fm/blob/b6ac1e9d60e18e594fb6310ec8a68d9ae683e2b2/manifm/model_pl.py#L355).

In the solver, `local_coords=True` selects exponential Euler; `local_coords=False, projx=True` selects ambient Euler followed by projection, a sphere retraction. With both false the numerical state can drift even though the field wrapper evaluates at its projected point. These flags describe source behavior, not our selected inference settings. [RFM integrator and Euler step](https://github.com/facebookresearch/riemannian-fm/blob/main/manifm/solvers.py), [field wrapper](https://github.com/facebookresearch/riemannian-fm/blob/main/manifm/model/arch.py).

RFM imports `ProductManifold` directly from Geoopt, rather than defining a local chunk-specific class. Its environment lists an **unpinned** `geoopt` dependency. [RFM imports](https://github.com/facebookresearch/riemannian-fm/blob/main/manifm/manifolds/__init__.py), [environment](https://github.com/facebookresearch/riemannian-fm/blob/main/environment.yml).

For inherited operations, this audit also inspected current upstream Geoopt source, **not a verified historical RFM environment**. `Sphere.inner` is the ambient dot product restricted to tangents; `proju` removes the radial component; `projx` normalizes; `expmap` uses the spherical exponential with a small-vector branch; `logmap` and `dist` contain numerical cutoffs. `random_uniform` normalizes an isotropic Gaussian ambient draw. That distribution differs from exponentiating a Gaussian in one fixed tangent plane. [Geoopt `sphere.py`, mutable `master`, accessed 29 October 2026](https://github.com/geoopt/geoopt/blob/master/geoopt/manifolds/sphere.py).

Geoopt's `ProductManifold` packs factor coordinates into a flat array, sums factor inner products and delegates projection, exponential/logarithmic maps and transport to individual factors. A flattened array is therefore compatible with a product manifold; normalizing the **whole** flat array would instead impose the wrong geometry. [Geoopt `product.py`: `inner`, `projx`, `proju`, `expmap`, `logmap`, `transp`, mutable `master`, accessed 29 October 2026](https://github.com/geoopt/geoopt/blob/master/geoopt/manifolds/product.py).

## Small corrections to the methodology

The following equations are our explicit interpretation/specialization for the approved chunk method, not claims that the RFM repository implements original RFMP LASA training.

1. **Define the manifold, tangent bundle and metric once.** For a chunk of `m` unit directions,

   ```text
   M = (S²)^m,  X = (x_1,...,x_m),
   T_X M = {W=(w_1,...,w_m): x_i^T w_i=0 for every i},
   g_X(W,Z) = sum_i w_i^T z_i.
   V_theta(s,X|o), U in T_X M.
   ```

   `M` has intrinsic dimension `2m`, while an ambient storage vector has `3m` entries. The time/context-conditioned field is a section of the tangent bundle for each fixed time/context. Tangent projection acts factor by factor. Context directions may be stored in ambient coordinates; scalar time/history offsets remain scalars. No chart conversion or transport of position-valued context is required merely to condition an MLP.

2. **Make the training target's base point explicit.** Write

   ```text
   X_s = Exp_(X_0)(s Log_(X_0)(X_1)),
   W_s = dX_s/ds in T_(X_s) M,
   L = E[ g_(X_s)(V_theta(s,X_s|o)-W_s,
                         V_theta(s,X_s|o)-W_s) ].
   ```

   Product maps act factorwise. The derivative may follow the verified JVP construction. Both vectors being subtracted live at `X_s`, so the FM loss requires no parallel transport. The loss's overall normalization remains an explicit reproduction detail, not a different geometry. Coincidence and cut-locus handling must preserve the source-to-data meaning; library clipping is not a mathematical resolution of a nonunique antipodal logarithm.

3. **Identify the CBF norm and pairing with that same metric.** The existing `a_i=-(I-x_i x_i^T)c` is already the Riemannian gradient for the induced round metric. Its dot product with `V_i+U_i` is the intrinsic directional derivative. The minimum-change cost is `g_X(U,U)/2`; the existing factorwise correction follows from this metric and the independent constraints. This adds precision without changing the approved filter. The nominal field can still couple all chunk positions. Changing factor weights would change the optimization and is not implied by this clarification.

4. **Name the actual manifold update without borrowing unsupported source settings.** The methodology's exponential update means

   ```text
   X_next = Exp_X(Delta_s * (V_theta + U)).
   ```

   Each finite step then ends on the product of spheres in exact arithmetic, with numerical drift still checked. Tangency alone does not make an ambient addition stay on the manifold. Point normalization is a different update; source support for one cannot certify the other. No step count, tolerances or activation schedule is selected by this audit. Neither update turns waypoint safety into connecting-arc safety.

5. **Give the existing diagnostics geometric definitions.** Use spherical distance for adjacent jumps, task-goal error and paired nominal/steered position displacement; use the product norm for intervention magnitude. Check per-factor norm error, tangency residuals and finite values for both `V` and `U`. The barrier residual remains `g_(x_i)(a_i,V_i+U_i)+phi*h_i`. These make the already requested diagnostics concrete without adding a new experiment. If roughness means comparing velocities based at different positions, transport them to one tangent space before subtraction and state the chosen connecting geodesic. If it only means adjacent angular jumps, no transport is needed. Do not label differences of raw ambient vectors at different points as intrinsic acceleration.

## Attribution and verification limits

Keep the approved repeated-point wrapped-Gaussian source attributed to the **RFMP paper**, as the methodology currently does. The generic RFM implementation does not resolve RFMP's Gaussian parameter convention, horizon indexing, observation/context assembly, LASA embedding or rollout bookkeeping. Also, repeating one sampled point across `m` factors is a correlated, diagonal-supported source, not an independent product draw. Do not copy generic full-dimensional base log-density/likelihood machinery and claim it describes that source. This observation does not authorize replacing the approved prior.

Successful reads: official RFM `sphere.py`, `utils.py`, `arch.py`, `solvers.py`, `__init__.py`, `environment.yml` at `main`; `model_pl.py` at both `main` and the pinned revision; upstream Geoopt sphere/product source at `master`. Failed reads: GitHub commits API, proposed local `manifolds/product.py`, local `manifolds/productmanifold.py`, `requirements.txt`, and pinned raw sphere/utils URLs. Failed URLs are **unverified**, not negative evidence about all possible repository versions. The import and environment files supply the actual dependency location. Newer `facebookresearch/flow_matching` was not needed and was not audited. No official original-author RFMP LASA implementation has been established by this audit.

The five clarifications above are sufficient to keep the core method in manifold language. They require no new model family, geometry framework, whole-trajectory formulation or expansion of the approved project.
