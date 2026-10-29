# LASA flow-matching implementations and endpoint choices

Research checked 29 October 2026. This is source research, not a reproduced experiment. No installation, training, dataset download, or implementation was performed.

## Result and evidence limit

I did **not verify a public original-author LASA flow-matching implementation with an inspectable loader and inference entry point**. The closest reference is Braun, Jaquier, Rozo and Asfour's *Riemannian Flow Matching Policy for Robot Motion Learning* (IROS 2024). Its LASA methodology is available. The related, later RFMP/SRFMP [official project site](https://sites.google.com/view/rfmp) supplies a paper and videos rather than a verified source repository. Consequently, the RFMP rows below describe the **paper**, not audited executable behavior. Absence of a verified repository is not proof that none exists.

## Original RFMP: what the paper actually specifies

Source: [author-hosted paper](https://h2t.iar.kit.edu/pdf/Braun2024.pdf), [arXiv HTML, sections III–IV](https://arxiv.org/html/2403.10672v2).

| Question | Paper-derived answer |
| --- | --- |
| LASA data | Seven demonstrations per shape; 200 time steps per demonstration. |
| What one flow sample represents | A short action chunk, not a complete demonstration and not an autonomous physical vector field. Default prediction horizon 8; execution horizon half the prediction horizon; horizons 2, 4, and 8 are compared. |
| Euclidean source | Gaussian with reported scale parameter σ=1. |
| Sphere source | Wrapped Gaussian at the north pole, reported scale σ=0.5, covering roughly a hemisphere. One sampled prior action is repeated across the action horizon. |
| Sphere mapping | LASA is normalized and projected onto the sphere; an exact coordinate mapping is not sufficiently specified in the experimental description to reproduce confidently. |
| Conditioning | Previous/current available observation and a randomly chosen earlier observation, accompanied by their time separation. |
| Inference | Sample a source chunk, integrate the generation flow, execute the initial part, and replan. |
| Start | A demonstration initial observation or a nearby sampled initial observation initializes reproduction. This is observation conditioning, not an explicitly described hard clamp on the generated chunk. |
| Final physical goal | No explicit final-goal input or final-waypoint clamp is described in this algorithm. Goal behavior is learned from demonstrations. |
| Split | 80/10/10 is reported. The split unit—whole demonstrations versus extracted examples/windows—is not verified. Do not call it a held-out-demonstration evaluation. |

The action-horizon indexing in the paper is inclusive in places; inspect eventual author code before asserting whether a horizon parameter counts points or transitions. **Generation endpoint** means a demonstrated action chunk; it does not mean the final physical task goal. Endpoint normalization alone would not establish hard pinning.

## Other actual LASA papers: code not verified

- [*Faster Visuomotor Policy Learning on Action Manifolds via Riemannian MeanFlow*, arXiv:2609.30127v1](https://arxiv.org/html/2609.30127v1), uses spherical LASA, seven 200-step demonstrations per shape, ten selected characters, a uniform hemisphere prior, and conditional action chunks. Its endpoint prediction predicts the flow's data sample, not an explicit physical final-waypoint constraint. No official code link, loader, or inference implementation was verified. This is a different paper from the publicly indexed `Riemannian-MeanFlow` repository by Woo and colleagues; that repository is not evidence of a LASA implementation of this paper.
- [*Let the Dynamics Flow* project site](https://let-the-dynamics-flow.github.io/SFMDS/) describes LASA, but its inspected code link does not identify a verified repository. Do not report an available implementation from this page.
- [*XFlowMP*, arXiv:2512.00022](https://arxiv.org/html/2512.00022v1), describes LASA and endpoint conditioning. The earlier [FlowMP repository](https://github.com/mkhangg/flow_mp) is not verified as its LASA implementation. An [author-repository issue asking about XFlowMP release](https://github.com/mkhangg/flow_mp/issues/1) is evidence of a release request, not an implementation. No loader or hard-clamp behavior was verified.

## Public code inspected that should not be presented as LASA evidence

### Streaming Flow Policy

The [official repository](https://github.com/siddancha/streaming-flow-policy) is public. Its documented examples are toy, PushT, and Franka; the [notebook index](https://siddancha.github.io/streaming-flow-policy/notebooks/) identifies the toy examples as synthetic one-dimensional configuration spaces. I did not verify LASA data handling.

Actual code still clarifies an endpoint distinction. [`sfp_aspace.py`, `muSigma0` and `v_conditional`](https://github.com/siddancha/streaming-flow-policy/blob/main/streaming_flow_policy/core/sfp_aspace.py#L74-L111) centers a Gaussian prior at each reference trajectory's initial point, with covariance controlled by `sigma0`. Its conditional velocity is

\[
v(t,a\mid\xi)=\dot\xi(t)-k\bigl(a-\xi(t)\bigr).
\]

Thus a conditional trajectory's error decays as \(e^{-kt}\); a nonzero initial error does not disappear exactly at a finite horizon. [`sfp_base.py`](https://github.com/siddancha/streaming-flow-policy/blob/main/streaming_flow_policy/core/sfp_base.py) integrates the marginal velocity from supplied initial samples; its inspected integration routine does not overwrite the first or final point with endpoint constraints. These are **generic implementation facts, not LASA results**. Links point to a mutable branch, inspected on the date above.

### Other exclusions

- [Sprague et al., *Stable Autonomous Flow Matching*, experimental section and appendix](https://arxiv.org/html/2402.05774v1) uses synthetic moons/circles in the inspected experiments, so it is not a verified LASA FM implementation.
- [KCDS's author repository](https://github.com/bbg-sjtu/KCDS) advertises LASA experiments including FM augmentation, but the relevant source files were not successfully inspected. It cannot support a claim about source sampling or endpoint enforcement here.
- `rfmp-ellipsoids` is an SPD/ellipsoid experiment, not verified LASA code; exclude it from the LASA comparison.

## Implication for the proposal

**Design inference:** We can choose explicit start/goal pinning for a whole-trajectory LASA experiment, but should describe it as our own design choice. The audited evidence does not establish that original RFMP pins both physical endpoints. RFMP's source chunk and observation-conditioned receding-horizon generation also differ materially from sampling an entire trajectory on a product of spheres. A comparison must distinguish learned endpoint accuracy from satisfaction of an imposed endpoint constraint.
