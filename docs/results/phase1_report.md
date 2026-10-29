# Phase 1 baseline — spherical LShape RFMP

29 October 2026. **Completed and validated: 35/35 autonomous rollouts pass the unchanged approved freeze gate.** The learned checkpoint and its data/split/draw/configuration records are frozen locally. Phase 2 is not implemented.

![Actual conditional spherical transport](flow_transport.png)

[Vector PDF](flow_transport.pdf) · [Autonomous rollouts and learning curves](rollout_diagnostics.png) · [Full manifest](phase1_baseline.json) · [All 35 rollout scores](phase1_rollouts.json).

Orange lines are the seven embedded recordings. Each blue point is the first predicted position of a joint eight-position chunk. Columns show the **same samples** at generation times 0, 0.5 and 1. Rows use validation-window and test-window conditions, not RFMP and SRFMP. There are 600 samples per row; the approved prior has not been narrowed for visual effect. The source pole coincides with the mapped demonstration goal, so this source cloud is deliberately broader than the supplied paper illustration. Generation time is distinct from execution along a motion; this density picture alone does not establish rollout performance.

## Measured results

The evaluation uses each of seven recorded two-position bootstrap histories with five source-noise seeds, yielding 35 attempts. Each then generates its own history, predicts eight future directions and uses four before replanning, for 200 retained positions. No future recorded direction is supplied after bootstrapping; no endpoint is pinned. All attempts are retained in the denominator.

| Metric | Mean over 35 attempts | Worst attempt | Approved per-attempt threshold |
| --- | ---: | ---: | ---: |
| Terminal angular goal error | 1.198° | 2.003° | ≤5° |
| Mean angular DTW error | 1.346° | 3.171° | ≤10° |
| Largest adjacent angular jump | 1.303° | 2.055° | ≤20° |
| Unit-norm residual | 8.51e-08 | 1.19e-07 | ≤0.00002 |

All 35 are finite and manifold-valid, and all jointly satisfy the three motion-quality thresholds. The required joint success fraction was at least 80%. This is a measured baseline acceptance result, not a theoretical convergence guarantee.

Training used **200 epochs, 109,739 context pairs per epoch and 171,600 optimizer steps**. Fixed-bank EMA validation loss fell from 10.935152 to **0.038979**, selecting epoch **192**. The separate fixed test-bank loss is **0.084126**. Loss is the batch mean of squared tangent errors summed over the eight sphere factors. The five-hidden-layer, width-64 model has 20,317 parameters, rather than claiming the paper's approximate parameter count.

Fitting took 572.45 seconds (9.54 minutes) on two CPU threads; combined autonomous rollout and scoring took 2.76 seconds. Plot generation is excluded from those timings. The environment is Python 3.12.7, PyTorch 2.9.1+cu128, NumPy 2.3.5, SciPy 1.16.0 and Matplotlib 3.10.6. CUDA was unavailable.

## Geometry and implementation checks

Learning and sampling remain on `(S²)^8` with its canonical product metric. Source-to-data paths are shortest spherical geodesics; tangent targets come from differentiation with `torch.func.jvp`. The neural output is projected into the current tangent fiber before the metric loss or integration. Sampling uses 100 factorwise sphere-exponential Euler steps. There is no SO(3) lift or ambient-Euler replacement.

Sixteen public-interface tests passed through one-behavior-at-a-time red–green cycles; see the [TDD log](../phase1_tdd_log.md). Actual saved-checkpoint reload reproduced the 1,200 plotted conditional chunks with maximum coordinate difference **0.0**. Re-evaluating saved rollout positions reproduced every saved score exactly. Over all factors of plotted snapshots at s=0,0.5,1, the largest tangent-field residual was 6.09e-06, and the largest unit-norm residual was 1.19e-07; both are below the numerical tolerance 0.00002. These are numerical checks, not safety guarantees.

## Data, provenance and reproduction limits

Input is the official [LASA LShape file](https://raw.githubusercontent.com/epfl-lasa/LASAHandwritingDataset/master/DataSet/LShape.mat): 355,828 bytes, SHA-256 `3aa960ed9241d4651c7e21240d63d616d215d889e08ce780fc7a5b1334474ce9`. It contains seven finite 2×1000 position arrays with strictly increasing time samples and endpoints at the origin. Cite and respect the [LASA dataset's academic-use terms](https://github.com/epfl-lasa/LASAHandwritingDataset); raw and transformed records are not bundled here.

We resample each recording to 200 normalized-time positions, then apply the sphere exponential at the north pole to scaled planar positions. The training-derived embedding scale is `0.01809553491727453`, with a maximum training radius of 60°. Split counts are 1,108 training, 138 validation and 140 test **recording/reference windows**, partitioned before context expansion. Underlying recordings and nearby positions overlap partitions. This is within-recording reconstruction, **not held-out-recording generalization**. Thirty-five rollouts represent only seven distinct recorded starts and five random seeds, not 35 independent demonstrations.

This independently reimplements the [original RFMP paper](https://arxiv.org/abs/2403.10672). Exact author LASA code was not verified. Embedding, split unit, horizon indexing, Gaussian covariance interpretation, layer counting, bootstrap/padding, normalization and integration details are explicit local conventions in the [approved specification](../../.scratch/rfmp-phase1/spec.md). The result does not establish equality to the authors' reported performance, stable RFMP/SRFMP reproduction, physical robot control or deformable-object manipulation.

## Preserved failure and approved correction

The initial run remains at `runs/phase1-baseline/`: 200 epochs over only 1,108 window samples each gave just 1,800 optimizer updates and **0/35** successful rollouts. Its best validation loss was 7.162889. It is retained as a failed experiment, not silently replaced.

Before retraining, the applicant approved enumerating every valid earlier context for each fixed training window. This changed the per-epoch coverage to 109,739 examples and the total to 171,600 updates. The model, prior, learning rate, EMA, validation bank, 200-epoch count and freeze thresholds were unchanged. This is the sole approved training-protocol correction; there was no architecture search or threshold relaxation.

## Frozen artifacts and commands

Training/sampling code reference: `f975c5e327e5f1d328c073ce12fdd72f945d9359`; local baseline tag: `phase1-rfmp-lshape-v1` (created after the report commit). Actual module hashes, full split indices, canonical split hash, hyperparameters, runtime versions and SHA-256 hashes of all frozen artifacts are in [phase1_baseline.json](phase1_baseline.json). Checkpoint SHA-256: `e4ba8a46ebc3dc635094b89e96e38ef1dc56902e127ea5ab349b07c8001c70ca`.

The ignored local directory `runs/phase1-context-expanded/` preserves `best.pt`, `banks.pt`, `training_pairs.pt`, full training history, rollouts with their context/source histories, evaluation, exact plotted sample banks and PNG/PDF outputs. The source data and checkpoint must be supplied separately when cloning this repository. Report figures and aggregate/per-attempt results are tracked; there has been no remote publication in this implementation step.

From the repository root, use the commands in the [README](../../README.md). To reproduce the additional freeze checks and JSON manifest without fitting, run:

```bash
MPLCONFIGDIR=runs/phase1-context-expanded/matplotlib-cache PYTHONPATH=src \
  /home/chengrui/miniconda3/envs/latentSafety/bin/python \
  .scratch/rfmp-phase1/freeze_checks.py
```

**Phase 1 is complete.** Phase 2 still requires its numerical specification/tickets and the agreed approval workflow. The current model has no safety steering. Connecting arcs, physical dynamics consistency and hardware validation remain outside the claims.
