# LASA FM/diffusion design decisions

Checked 29 October 2026. Reading only; no implementation, installation, dataset generation, training or inference. This review does not approve project design choices.

## Most relevant LASA comparison

Braun, Jaquier, Rozo and Asfour's **Riemannian Flow Matching Policy for Robot Motion Learning** directly compares RFMP and Diffusion Policy on LASA, including spherical motions. Its Sections III–IV establish these choices:

| Decision | Reported LASA RFMP choice |
| --- | --- |
| Generated quantity | Short sequence of future **positions** on R² or S², called actions; not angular velocities |
| Conditioning | Reference position, a sampled earlier context position, and their time-index separation |
| Sequence use | Predict a chunk, execute a shorter part, observe and regenerate |
| Horizon | Default prediction 8, execution half; compare prediction horizons 2, 4 and 8 |
| Data | Seven demonstrations, 200 time steps per demonstration |
| Sphere source | Wrapped Gaussian at north pole, reported scale 0.5; repeat one sampled source position across the chunk |
| Endpoint constraint | No explicit start-and-goal pinning construction in the described sampler |
| Network | Small MLP; manifold Euler integration |
| Split | Reported 80/10/10; original-demo versus window split unit not established |

The diffusion comparison uses the same prediction/execution horizons and 100 denoising iterations. Both reconstruct motions by sequentially executing generated chunks. These are **paper-reported implementation choices**: an author LASA loader/trainer/sampler was not verified. [Primary paper, Sections III–IV](https://arxiv.org/html/2403.10672v1#S3)

## What actual released code establishes

| Source | Evidence inspected | Limit |
| --- | --- | --- |
| [Official Diffusion Policy low-dimensional policy](https://github.com/real-stanford/diffusion_policy/blob/main/diffusion_policy/policy/diffusion_unet_lowdim_policy.py) | Gaussian source; observation conditioning through local/global inputs or an inpainting mask; returned action-window slicing | Generic upstream source, not the RFMP authors' LASA configuration |
| [Official Spline Policy](https://github.com/mengze3/spline_policy) | LASA-derived S sequence loaded and spline-encoded in its demonstration notebook; diffusion/FM policy files exist | Inspected notebook's training command uses Push-T; LASA diffusion/FM training-to-sampling chain not verified |
| [Official SAD-Flower sampler](https://github.com/TzuYuan107/sad-flower/blob/main/gflower/models_flow/flow_policy.py) | Specified state coordinates are conditioned and their generation derivatives are zeroed | Supports hard planning boundary conditions; its Maze2d start/goal setup is not a LASA experiment |

In upstream Diffusion Policy, `conditional_sample` reimposes masked coordinates each iteration and at return. However, `predict_action` uses an all-false action mask for local/global observation conditioning, or masks only observed history features for inpainting. The generic mechanism does **not** itself pin a future action goal. [Raw implementation](https://raw.githubusercontent.com/real-stanford/diffusion_policy/refs/heads/main/diffusion_policy/policy/diffusion_unet_lowdim_policy.py)

Separate detailed audits: [FM sources](lasa_flow_implementations.md), [diffusion sources](lasa_diffusion_implementations.md). Unverified source availability is not proof that code does not exist.

## Implications for SafeManifoldFlowMatching — our design judgment

1. The earlier “actions versus S² states” distinction needs care: RFMP's actions can themselves be manifold **positions**. Our real adaptation is **complete planned sequence versus repeatedly generated short chunks**. Keep the agreed complete-sequence formulation.
2. Hard start-and-goal pinning follows our boundary-constrained planning objective and SAD-Flower, not an established LASA RFMP convention. If selected, learning is judged by the interior LShape geometry and variation; exact endpoint arrival is imposed.
3. If we instead want to evaluate learned target arrival, fix the start and let the terminal point be generated, then measure terminal angular error. This adds a learned requirement and allows Phase 2 to move the goal unless an additional constraint is specified. No endpoint option is approved yet.
4. A hemisphere-scale source is supported by the RFMP example. “Unconstrained by the forbidden cone” does not require uniform noise over the entire sphere. Choose the prior explicitly; preserve it across phases.
5. Do not copy repeated-single-point noise or window-based data counts blindly into a full-sequence model. Prior dimensionality, model size and the scarcity of independent demonstrations need their own justification. Seven original recordings remain seven independent full-sequence examples.
6. Retain the already agreed original-demo split before augmentation. The paper's percentage alone does not establish that split policy. Do not infer learned generalization from many overlapping windows or transforms of the same held-out recording.

Translating demonstration endpoints to a common coordinate origin, supplying a goal to a network, and hard-clamping a generated endpoint are three different operations. The specification must identify which operations we use.
