# Flow matching and stability: proposal research

Checked 29 October 2026. Research only: no model installation, dataset download, implementation, training or experiments were performed for this task. This note supports an unapproved proposal and must not be described as applicant project experience.

## Papers and reading scope

The supplied **Flow Matching on General Geometries** is Chen and Lipman, ICLR 2024, arXiv:2302.03660v3 (26 February 2024). I read the manifold objective, premetric construction and geodesic specialization (Sections 2–3), experiments, proofs in Appendices B/C, and the sphere/parameterization/numerical details in the appendices. [Paper](https://arxiv.org/abs/2302.03660), [ICLR proceedings](https://proceedings.iclr.cc/paper_files/paper/2024/hash/d1f9936d3be6997ffffab692977eebe6-Abstract-Conference.html).

The supplied **Fast and Robust Visuomotor Riemannian Flow Matching Policy** is Ding, Jaquier, Peters and Rozo, arXiv:2412.10855v3 (7 August 2025). I read Sections III/IV, Algorithms 1/2, implementation details, sphere experiments and conclusions. The PI's publication list gives the final citation as IEEE Transactions on Robotics 41, 5327–5343 (2025). Do not confuse it with Braun et al.'s earlier **Riemannian Flow Matching Policy for Robot Motion Learning**, IROS 2024. [2025 paper](https://arxiv.org/abs/2412.10855v3), [PI publications](https://njaquier.ch/?page_id=74), [authors' project page](https://sites.google.com/view/rfmp).

## What ordinary RFM learns

For a manifold `M`, the learned field must satisfy `vθ(t,x) ∈ TxM`; its regression loss compares tangent vectors using the Riemannian metric. RFM marginalizes per-data-point conditional flows. For simple manifolds, training samples and target velocities can be computed from a geodesic without an ODE solve. This is a density-transport construction, not a motion-planning safety result. Chen/Lipman Equations (8)–(15), Proposition 3.2 and Appendix C establish the connection. [Paper](https://arxiv.org/abs/2302.03660)

For sphere points `x0,x1` away from antipodal ambiguity, the correctly directed ordinary conditional path is:

```text
x(t) = Exp_x0(t Log_x0(x1))
     = Exp_x1((1-t) Log_x1(x0)),    t in [0,1]
u(t,x(t)|x1) = d x(t)/dt ∈ T_x(t) S².
```

One can compute the derivative by a geodesic Jacobian-vector product (JVP), or equivalently use `Log_x(t)(x1)/(1-t)` away from the terminal singularity. Ambient neural outputs can be projected with `P_x = I - x xᵀ`; on the round unit sphere the tangent metric is the ambient dot product. Sphere exponential/logarithm formulas are in Chen/Lipman Table 5. Endpoint limits, near-coincident points and the antipodal cut locus need explicit handling in the eventual specification.

**Paper convention discrepancy:** Ding et al. Equation (8) prints `Exp_x1(t Log_x1(x0))`, which reverses the stated source/target endpoints. Chen/Lipman Equation (15) has the decreasing scheduler `κ(t)=1-t`. Official Meta code resolves ordinary direction by constructing `geodesic(x0,x1)` and differentiating it. This is a reason to test endpoint and tangent identities against independent examples rather than copy displayed formulas mechanically. [Official geodesic helper](https://github.com/facebookresearch/riemannian-fm/blob/main/manifm/manifolds/utils.py), [training target implementation, lines 553–565](https://github.com/facebookresearch/riemannian-fm/blob/main/manifm/model_pl.py#L553-L565).

## What Stable RFMP adds, and what it does not establish

RFMP generates an **action sequence** on a product manifold, conditioned on observation history. The generation process has its own ODE time; only after generation are the first actions executed in a receding-horizon loop. Thus generation-time convergence to an action-distribution support is not a theorem that the physical robot reaches a task goal. Ding et al. Section IV-A and Algorithm 1 make this separation explicit. [Paper](https://arxiv.org/abs/2412.10855v3)

SRFMP augments the generated state with pseudo-time `τ`, creating an autonomous field on `M × R`. Its conditional targets use an exponentially contracting path:

```text
x(s) = Exp_g(exp(-λx s) Log_g(x0))
τ(s) = τ1 + exp(-λτ s)(τ0-τ1).
```

The spatial target approaches `g` **asymptotically in continuous generation time** `s`. Both the spatial field and pseudo-time field are learned; implementations described in Section V-A replace the usual time conditioning by a pseudo-time embedding and add an MLP for its derivative. `τ0=0`, `τ1=1` and `λx=λτ=2.5` are the reported defaults, not mandatory choices for our project. Equation (22) regresses the augmented field under a Riemannian metric. [Paper, Sections IV-B/V-A](https://arxiv.org/abs/2412.10855v3)

**Tangent-anchor discrepancy that matters for S²:** Equations (19)/(20) write a negative logarithm anchored at the target. Such a vector belongs to `T_g M`, whereas the state derivative must belong to `T_x M`. On the sphere, differentiating the displayed path yields the well-typed field `u_x = +λx Log_x(g)` away from the cut locus. Equivalently, the negative goal-anchored log must be parallel transported along the selected geodesic. Equation (25) itself uses the current-point expression `+λx Log_x(g)`. No verified official SRFMP implementation was found to disambiguate its actual training code. Treat this as a notation issue to resolve through derivation, not permission to subtract tangent vectors at different points.

The paper's one-step argument sets a projected/exponential Euler step to `Δs=1/λx`. Exact arrival then requires the exact conditional contraction field. Equations (23)–(25) explicitly assume perfect learning and distinguish that ideal argument from empirical neural performance. It is not finite-time convergence of the continuous exponential path, and it is not an unconditional guarantee for an observation-conditioned, approximately learned marginal field. A CBF correction further changes that field, so the nominal argument cannot simply be inherited.

## Official resources checked

| Resource | Verified status and useful scope |
| --- | --- |
| [Original Meta RFM repository](https://github.com/facebookresearch/riemannian-fm) | Official paper implementation; archived/read-only since 6 August 2025. Supports sphere, torus, SPD, hyperbolic, Euclidean and mesh manifolds. README links data preparation, not pretrained models. |
| [RFM environment](https://github.com/facebookresearch/riemannian-fm/blob/main/environment.yml) | Python 3.9, PyTorch/CUDA 11.7, Lightning 1.8.5.post0, Hydra 1.2, Geoopt and Torchdiffeq, plus mesh/geospatial dependencies. Entire environment reproduction is unnecessary for a sphere-only prototype and introduces setup risk. |
| [Sphere code](https://github.com/facebookresearch/riemannian-fm/blob/main/manifm/manifolds/sphere.py) | Wraps Geoopt sphere, supplies uniform prior and explicit parallel transport. Useful reference for geometry and conventions; numerical handling still needs independent checks. |
| [RFM dataset link](https://rtqichen.com/manifold_data/data.zip) | Linked by official README; browser retrieval failed on redirect. Archive contents/current availability were not verified. Paper sphere datasets concern earth/climate density modeling, not constrained robot pointing demonstrations. |
| [RFM license](https://github.com/facebookresearch/riemannian-fm/blob/main/LICENSE) | CC BY-NC 4.0. Record attribution and provenance if adapting code; do not present copied routines as original applicant contributions. |
| [RFMP/SRFMP official project page](https://sites.google.com/view/rfmp) | Paper and video verified. It currently summarizes eight tasks, whereas the supplied v3 paper evaluates ten; use the supplied v3 for method/experiment details. No official code repository, custom Sphere Push-T dataset download, license or pretrained checkpoint was verified. Search failure is not proof that none exists. |
| [Newer official Meta Flow Matching library](https://github.com/facebookresearch/flow_matching) | Current README requires Python ≥3.9 and PyTorch ≥2.1, includes Riemannian examples and says it does not release pretrained models in this version. It is adjacent tooling, not SRFMP's implementation. Code is CC BY-NC licensed. |
| [Newer geodesic probability path](https://github.com/facebookresearch/flow_matching/blob/main/flow_matching/path/geodesic.py) and [sphere utilities](https://github.com/facebookresearch/flow_matching/blob/main/flow_matching/utils/manifolds/sphere.py) | Direct geodesic/JVP targets, tangent projection, exponential/log maps are available for reference. The linked Riemannian example is a flat-torus notebook, not a ready-made safe-sphere robotics task. |

## Proposal implications — our inference

1. **A direction on S² is a suitable small robotics abstraction:** camera/sensor/tool pointing with forbidden viewing directions. It does not encode roll or full SO(3) orientation, and it does not by itself demonstrate deformable manipulation.
2. **Choose the meaning of a trajectory before designing FM.** A density-generation path from random noise to a target sample is not automatically the physically executed pointing path. Options are a direct learned tangent motion field, or an FM sampler of action/waypoint sequences with a separate execution controller. State which one is implemented and tested.
3. **Learning must have a nontrivial job.** If the task is only a fixed target with one forbidden cap, analytic geodesic attraction plus a CBF already supplies a strong baseline. A learned route/style or multimodal safe demonstration distribution can make the learning component meaningful. Avoid calling an analytic target field a trained policy.
4. **Separate claims:** tangent projection and geometric integration address manifold adherence; a correctly posed CBF addresses continuous-time invariance under its assumptions; convergence requires an additional compatible argument or empirical evaluation. Filtering may create equilibria on a cap boundary, alter multimodal coverage, or change the generated distribution.
5. **A realistic ≤18-hour core is synthetic state-conditioned S², not a visuomotor reproduction.** Reuse the mathematics and small verified geometry routines; avoid image backbones, Robomimic/Franka setup, full Sphere Push-T recreation or dependence on unverified checkpoints. Synthetic demonstrations need transparent generation rules, train/test splits and an analytic baseline. Actual project scope remains the applicant's decision through grilling and proposal approval.

The first design decision should therefore establish whether the project demonstrates a learned **physical pointing controller** or a safe **generative action/trajectory sampler**. The same symbol `t` should not hide these different time axes.
