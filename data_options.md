# Demonstration-source choice: synthetic sphere paths or LASA

29 October 2026. **Decision: the applicant selected LASA LShape for initial trials.** The comparison below preserves the design rationale. No dataset has been downloaded, generated, transformed or used for training.

**Later decision:** Phase 1 reimplements original RFMP's LASA method and inherits its documented settings. It uses 200-step demonstrations, observation-conditioned short position chunks and receding-horizon rollout. The original complete-trajectory proposal below is historical context; see the [current proposal](proposal.md) for the inherited settings and unresolved reproduction details.

## What the two choices contain

**Synthetic spherical trajectories:** we define a small procedural family of complete pointing motions directly on S². Inputs might include start/goal directions, a curvature parameter and an approach style. A suitable construction would generate curved paths rather than only the shortest geodesic, and could provide multiple modes. The construction itself must be documented; it is not human demonstration data.

**LASA mapped onto S²:** use recorded human handwriting demonstrations as the source of path shape, then embed their 2D coordinates onto the sphere. The official LASA version 2.0 describes 30 motion families, seven demonstrations per family, with nearby but different starts and a shared endpoint. Each demonstration is stored with 1,000 interpolated samples, and position, time, velocity and acceleration records. [Official LASA repository](https://github.com/epfl-lasa/LASAHandwritingDataset), [EPFL dataset directory](https://www.epfl.ch/labs/lasa/code-datasets/).

The important distinction is **controlled procedural variation versus recorded human variation**. Either choice becomes a sphere-valued benchmark; neither is a dataset of robot pointing on hardware.

## How LASA would become spherical data

The earlier complete-trajectory discussion proposed the following embedding. It is **not verified as RFMP's exact mapping** and is not automatically inherited by the reproduction:

1. Keep the temporal order of each planar demonstration and resample it to our chosen waypoint horizon.
2. Center its terminal point at the planar origin.
3. Scale its extent to a documented angular range.
4. Interpret the two coordinates in an orthonormal tangent basis at the desired sphere goal and use the sphere exponential map.

The terminal origin then maps to the goal direction. Limit the tangent radius below the antipodal ambiguity and choose preprocessing from training data only. This creates curved paths on S², but it changes distances and temporal derivatives; original 2D velocities/accelerations cannot simply be reused as 3D quantities. Our selected state-only project does not need those derivative labels.

RFMP's supplied paper includes an L-shape LASA example mapped to the sphere in Figure 3, making this a relevant visualization reference. It is not evidence that the resulting dataset is real spherical robot motion or an exact reproduction of the paper's robotics benchmarks. [RFMP/SRFMP paper](https://arxiv.org/abs/2412.10855v3)

## Comparison for this project

| Aspect | Synthetic S² demonstrations | LASA embedded on S² |
| --- | --- | --- |
| Shape source | Explicit procedural rule | Recorded human motion |
| Variation | Can independently vary starts, goals, styles and curvature | Natural variation within a small set of recorded demonstrations |
| Number of original full sequences | Chosen through the generator | Seven per motion family in the official dataset |
| Learning question | Can FM learn a known, controlled trajectory distribution? | Can FM reproduce demonstrated path shapes and their variation? |
| Generalization experiments | Straightforward held-out parameter/task draws | Limited original demonstrations; augmentation and claims need care |
| Geometry preparation | Designed directly on the sphere | Requires normalization, embedding and a chosen angular scale |
| Debugging | Known intended structure and controllable difficulty | More preprocessing decisions and natural variability |
| Main limitation | Model may merely learn a simple hand-designed family | Few independent sequences; preprocessing can dominate behavior |
| Application wording | Learning from synthetic pointing demonstrations | Learning from human handwriting demonstrations embedded on S² |

## Chunk learning and independent recordings

One Phase 1 FM sample is now a **short future position chunk**, paired with RFMP's observation/context conditioning. Many training examples can be extracted from the seven original recordings, including overlapping chunks and different context pairs. They remain dependent samples from seven human demonstrations. The source dataset's 1,000 stored points are resampled to the paper's 200-step representation.

RFMP reports an 80/10/10 split without an established split unit in the inspected description. Resolve that unit explicitly in the spec. A window split cannot support held-out-recording claims; a whole-demo split of seven recordings cannot exactly match those percentages and must be labeled as a deviation. Do not add rotations/perturbations as inherited settings without source evidence; any transforms must retain source-demo provenance.

Synthetic data can supply many independent parameter draws, but its effective diversity is still limited by the generator's design. Generated quantity alone does not establish real-world generalization.

## Selected source and two-phase plan

Use **LASA LShape only** for the initial project. This prioritizes a recognizable recorded motion pattern with a clear sequence-imitation objective. Preserve the small-independent-sample limitation in evaluation and application wording.

The initial trial does not establish multi-skill, multi-family or real-world robot generalization. Any augmentation must be labeled and must not undermine the declared split unit. Do not silently expand to additional LASA families or a synthetic training study.

Avoid committing to two separate full training studies within 18 hours. Whichever source is chosen:

- **Phase 1:** reimplement RFMP's LASA method on LShape without safety; preserve the checkpoint, exact split unit/indices, preprocessing, configuration, rollout initialization and baseline generations.
- **Phase 2:** add generation-time safety steering to the same short position chunks, retaining RFMP's replanning loop and frozen Phase 1 model. The applicant approved this structure; numerical recovery and evaluation details remain under discussion.

If LASA is selected, check and respect its published data-use terms before packaging artifacts. The official repository permits noncommercial academic use with attribution and places restrictions on modification/distribution; do not assume transformed datasets can be bundled in a public repository. No external release is currently requested.

**Source and Phase 1 method decisions are settled.** Inherit RFMP's documented conditioning and training choices. Its exact mapping and split unit remain under-specified; resolve them explicitly. Source/method selection is not yet approval to download/transform data, train a model or begin implementation.
