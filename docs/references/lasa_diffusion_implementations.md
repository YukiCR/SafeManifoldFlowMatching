# LASA diffusion implementation audit

Checked 29 October 2026. Research-only review of primary repositories and their displayed source. No repository was installed, no dataset was downloaded, and no training, inference or tests were run. Current project choices remain subject to applicant approval.

## Finding

**Do not yet cite a verified LASA-loader → diffusion-training → endpoint-conditioned-sampling implementation from this audit.** Spline Policy is a relevant official implementation with LASA-derived demonstration data and diffusion/FM backbones, but the accessible LASA notebook demonstrates spline encoding, not training a LASA diffusion model. Exact conditioning and endpoint claims remain unverified where source fetches failed.

This distinction matters: a repository can contain LASA data and a diffusion backbone without the inspected example actually learning that data through diffusion.

## Spline Policy — relevant official repository, incomplete LASA training evidence

**Identity.** [Official repository](https://github.com/mengze3/spline_policy), accompanying *Spline Policy: A Structured Representation for Robot Policies*, Tian et al., [arXiv:2606.07386v2](https://arxiv.org/abs/2606.07386v2). The authors describe a representation in which a policy predicts spline parameters; they instantiate it with diffusion, FM and other backbones. Its released configuration names include ordinary and spline variants. This establishes the representation/backbone distinction, not a LASA endpoint policy.

**Actual LASA-derived source inspected.** The [raw demonstration notebook](https://raw.githubusercontent.com/mengze3/spline_policy/refs/heads/main/spline_policy/notebooks/spline_policy_demo.ipynb), first substantive data cell, calls `ReplayBuffer.copy_from_path` on `data/demonstrations/S.zarr`, requests the `action` key and selects episode 0. The comment records a `(1,20,2)` sequence. It fits that existing sequence into spline parameters using `encode_trajectory`, then reconstructs it. Later cells integrate a derived corrective vector field from perturbed starts. These are direct code observations; they are not evidence that a diffusion sampler generated the S trajectory.

The notebook's displayed training command instead uses the **Push-T** workspace and dataset. The [released task configuration listing](https://github.com/mengze3/spline_policy/tree/main/spline_policy/config/train/task) exposes can, Push-T and transport configurations; no LASA/demonstration task configuration was displayed in that listing. The [third-party notice](https://github.com/mengze3/spline_policy/blob/main/THIRD_PARTY_NOTICES.md) attributes demonstration data to LASA handwriting and lists inherited Diffusion Policy components.

### What can and cannot be concluded about start/goal treatment

| Question | Verified observation | Confidence |
| --- | --- | --- |
| Does the example load one point, a motion sequence or an action window? | It loads an existing two-dimensional action sequence from one stored S episode; the visible comment gives 20 points. This is sequence data, not a point-density/vector-field training example. Whether that stored episode represents a complete original LASA demonstration or a window was not established. | High for inspected sequence; unknown for original conversion |
| Is the notebook learning LASA through diffusion? | Its inspected LASA cell fits a spline to supplied waypoints. The visible training section is Push-T. | High: the notebook must not be described as demonstrated LASA diffusion training |
| Is a start observation used as conditioning during LASA diffusion? | The relevant LASA training/sampling path was not accessible. | Unverified |
| Is the first point pinned during denoising? | Not established by the inspected LASA example. | Unverified |
| Is a goal supplied or hard-pinned during denoising? | Not established. The notebook has no explicit goal-conditioning demonstration. | Unverified |
| Are LASA terminals translated to the origin? | Conversion/preprocessing source was not accessible. | Unverified |
| Does spline continuity imply endpoint clamping? | No. Inspected `set_boundary_condition` concerns continuity with a previous spline segment; it is not a start-and-goal denoising mask. | High |

The [quadratic spline source](https://github.com/mengze3/spline_policy/blob/main/spline_policy/policy/diffusion_policy/planning/quadratic_spline.py) contains `get_boundary_condition`, `set_boundary_condition`, and `encode_trajectory_given_w`. The continuity routine constructs new initial control points from the preceding spline. This is a downstream representation/continuity operation and must not be reinterpreted as a diffusion sampler's hard endpoint constraint.

### Exact implementation files identified but not read successfully

The [policy directory listing](https://github.com/mengze3/spline_policy/tree/main/spline_policy/policy/diffusion_policy/policy) verifies the following files exist:

- `diffusion_unet_lowdim_policy.py`
- `diffusion_unet_lowdim_spline_policy.py`
- `flowmatching_unet_lowdim_policy.py`
- `flowmatching_unet_lowdim_spline_policy.py`

Attempts to fetch their blob/raw contents failed in the browsing tool. The LASA/demonstration environment and dataset directories were also unavailable. Therefore this audit cannot responsibly specify their noise prior, observation mask, action-window extraction, normalization, or endpoint clamping based only on familiar upstream class names.

Repository links inspected here track `main`; an immutable commit hash could not be obtained from the accessible pages. Do not claim these findings are pinned to a particular commit. Pin and inspect a concrete revision before treating it as an implementation dependency.

## Generic upstream Diffusion Policy: verified sampling semantics

The upstream [DiffusionUnetLowdimPolicy source](https://raw.githubusercontent.com/real-stanford/diffusion_policy/refs/heads/main/diffusion_policy/policy/diffusion_unet_lowdim_policy.py) was accessible and inspected directly. **This is generic implementation evidence, not proof of a LASA experiment.**

- `conditional_sample` initializes a horizon-shaped Gaussian with `torch.randn`, iterates the diffusion scheduler, reapplies the conditioning mask each step, and reapplies it after the final step.
- With local/global observation conditioning, `predict_action` uses an all-false trajectory mask; observations are passed as model features.
- With inpainting, it masks only the first `n_obs_steps` of the **observation feature coordinates** in a joint action/observation sequence. The mask generator is configured with `action_visible=False`.
- The function extracts action coordinates and returns an action window; the usual slice begins at `n_obs_steps-1`, with an alternative indexing convention available.
- No explicit action-goal pin or hard action-start pin appears in this inspected function. A task could encode goal information in observations, but conditioning on such information would still differ from hard endpoint equality.

Confidence is high for this function's behavior. Dataset conversion, task-specific observations and any modifications in a LASA adaptation still need their own source evidence.

## Commonly confused candidates

- **SCDS** is [Contractive Dynamical Imitation Policies for Efficient Out-of-Sample Recovery](https://github.com/aminabyaneh/scds-contractive-imitation), ICLR 2025. It does train on LASA, but its model is a contractive dynamical system using recurrent equilibrium networks. It is **not** “Stable Contrastive Diffusion Policies.” It can inform stable dynamical-system evaluation, not establish a diffusion endpoint convention.
- **Stable Motion Primitives via Imitation and Contrastive Learning**, Pérez-Dattari and Kober, is [a dynamical-system imitation method](https://arxiv.org/abs/2302.10017), not a diffusion-policy method. The similarly worded proposed title “Stable Motion Primitives via Diffusion Policies” was not verified.
- **Contractive Diffusion Policies**, ICLR 2026, has an [official diffusion repository](https://github.com/aminabyaneh/contractive-diffusion-policy). The inspected README describes contraction regularization of reverse diffusion but does not establish LASA use. Do not transfer SCDS's LASA data handling to this distinct project.
- Search results for **Stable-Sim2Real on LASA** concern a large-scale aligned **3D shape** dataset, not EPFL LASA handwriting. They are irrelevant to the current motion-family decision.

## Consequence for our endpoint decision

This audit supports keeping three decisions separate:

1. **Data coordinates:** translating demonstration terminals to a common origin changes the coordinate frame; it does not enforce sampled terminal equality.
2. **Learned conditioning:** a model may observe current state/history or a goal and still generate endpoints with error.
3. **Hard constraints:** endpoint clamping/pinning requires explicit sampler-level masking, reduced variables, or another demonstrated constraint mechanism.

For our approved whole-trajectory/product-sphere direction, these must be specified directly. An upstream repository name alone does not determine them. The RFMP paper/source audit is the more direct reference for manifold-valued action windows; generic Diffusion Policy mechanisms should be labeled as such unless a concrete LASA training and inference path has been traced.

**Outstanding evidence needed before asserting an inherited convention:** an immutable source revision, raw LASA conversion, dataset/windowing code, training configuration, and actual conditional sampling function. Until then, Spline Policy remains a useful representation reference with partial LASA evidence, not a verified answer to start/goal handling in LASA diffusion training.
