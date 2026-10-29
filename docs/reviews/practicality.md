# Independent review: practicality and evaluation

29 October 2026, approximately 21:00 China time. Reviewed `methodology.md` independently, with the project rules, proposal, Phase 2 draft and existing LASA implementation audit as supporting context. No other review reports were read. No project code, imports, tests, dataset preparation, training or numerical trials were run. Line references below refer to the reviewed `methodology.md`.

## Overall verdict

The method is a coherent, small **conditional feasibility study**, with unusually clear separation between generation, execution acceptance and physical safety claims. It is ready for applicant review. Successful learning, numerical recovery and useful obstacle adaptation have **not** been demonstrated; the remaining schedule cannot support a promise that both phases will succeed.

Before implementation, preserve two methodology-level commitments: Phase 2 requires a useful frozen Phase 1 rollout baseline, and the project may finish with an honestly documented incomplete/negative result at the budget stop. Exact geometry, split, bootstrap, gains, thresholds and integration values are later specification decisions; their present absence is not a reason to replace the agreed method. The specification must settle them together before data preparation or training. No new model, dataset family, safe-prior restriction or physical controller is needed to resolve the findings below.

## Prioritized findings

### 1. High — The two-phase outcome is plausible, but not yet schedule-feasible evidence

**Affected:** §1, lines 10–15; §4, lines 62–68; §8, lines 148–154. Supporting evidence: proposal time-budget table and implementation audit.

Research began around 15:58 and this review began around 21:00: approximately five hours of the conservative preparation window have elapsed. The hard stop at 09:45 leaves about 12 hours 45 minutes of wall time at 21:00, slightly less than the nominal 13-hour post-preparation allocation. Applicant review, specification, ticket approval and further review consume this same window. There is no completed learning baseline or verified author LASA trainer to absorb unexpected debugging. Working compute and dependency imports have not been established by this review.

The inherited MLP and one-family data make a short training run plausible. This is an engineering expectation, not a measured runtime or evidence that 200 epochs will produce useful autonomous rollouts. Geometry, indexing and conditioning errors can consume more time than optimization. The singular recovery sampler is a second independent implementation risk.

**Minimal change:** treat the remaining schedule as a ceiling with explicit phase gates and stop conditions, not a guaranteed delivery plan. Retain the inherited 200-epoch choice for an attempted reproduction; do not promise a successful checkpoint or extend the deadline to obtain one. If Phase 1 fails its gate, preserve its artifacts and explain the failure; do not proceed using an unvalidated model or an analytic replacement. This needs a methodology-level commitment, while checkpoint times and numerical gate thresholds belong in the specification. An unfinished result must not be converted into a completed-project application claim.

### 2. High — “Validate motion learning” needs an operational rollout gate

**Affected:** §4, lines 45–68; §7, lines 138–140.

Seven recordings and many overlapping chunks can support learning this restricted motion family, but do not establish generalization. Low validation flow loss or plausible teacher-conditioned chunks do not show that repeated replanning works: small prediction errors alter later observations, and CBF steering moves them further from training histories. An apparent Phase 2 failure could otherwise be a broken nominal rollout.

**Minimal change:** require finite, manifold-valid nominal chunks and useful no-conflict receding-horizon progress from the declared supplied histories before freezing Phase 1. Include terminal error and excessive command jumps in that gate, with explicit horizon/end-of-rollout handling. Keep a small fixed seed suite; a second training seed is not essential for this time-limited case study. Do not require broad statistical generalization from seven recordings. Choosing grouped recordings versus windows and the exact thresholds is specification work; disclose the resulting claim boundary. A window split supports within-recording reconstruction evidence, not unseen-recording performance.

### 3. High — Margin, terminal cutoff and near-center behavior form one numerical design problem

**Affected:** §5, lines 90–122; §7, lines 136–138.

The document correctly rejects an exact finite-step recovery certificate. Practical failure is not confined to the exact zero-gradient point. At angular distance `r` from the forbidden center, `||a||=sin(r)`; near that center an active recovery correction can scale approximately as `phi(s) * (1-cos(theta_int)) / r`. Both small `r` and the terminally growing gain can therefore produce enormous angular updates. An exponential update preserves unit norm while still overshooting badly; norm checks alone will not diagnose this failure. A denominator epsilon or correction clipping silently changes the stated constraint unless residual violations are recorded.

The margin also provides a useful analytic planning check. Let `Delta=cos(theta)-cos(theta_int)>0`. Under the continuous inequality, valid throughout the controlled interval, a negative activation barrier `h_on` has lower bound `h(s_end)>=h_on*exp(-I)`, where `I=integral(phi)`. Thus `(-h_on)*exp(-I)<=Delta` is a sufficient continuous recovery bound for actual-cone safety at a finite cutoff. It is not a discrete guarantee, but connects margin and integrated gain without demanding evaluation at the singular endpoint.

**Minimal change:** specify activation, cutoff, grid, margin and a numerical-failure policy together. Record constraint residuals, near-zero-gradient failures and correction magnitudes; fail explicitly on unusable output. If finer integration is needed, retain the prescribed matched-grid nominal comparison. These are specification decisions, but discovering that no affordable setting yields useful recovery is a legitimate negative project result, not authorization to change the prior or add post-hoc repair.

### 4. Medium — Geometry, bootstrap and cap placement must be frozen as one reproducible scene

**Affected:** §4, lines 46–64; §5, line 72; §7, lines 138–140.

The unknown sphere embedding determines angular step sizes, endpoint clearance, cap size and proximity to numerical singularities. History bootstrap determines the first conditioning input and which part of the motion is actually generated. Terminal padding determines late-stage contexts and what “completion” means. These are coupled experimental choices, not interchangeable cosmetic preprocessing.

The stated route-conflicting cap should intersect returned nominal waypoints, rather than only connecting arcs; arc-only conflicts are outside the accepted claim. Start and demonstrated goal being outside the internal cap is necessary but does not ensure this local generation correction produces a useful detour. Boundary accumulation and stalled/out-of-distribution replanning remain plausible outcomes.

**Minimal change:** define the embedding and supplied history before choosing caps; define the goal from the corresponding embedded demonstration without adding goal conditioning or pinning. Freeze a small deterministic route-conflicting/no-conflict scene set before final evaluation, with development scenes kept distinct. Report all frozen scenes, including ones where nominal generation does not actually conflict or steering fails to progress. Exact scene coordinates and indexing belong in the specification; a larger obstacle sweep is unnecessary.

### 5. Medium — The comparison is fair in principle; success must combine avoidance with progress

**Affected:** §6, lines 126–132; §7, lines 136–142.

The same acceptance check on both methods, pre-acceptance rates, failure-inclusive denominators and matched-grid comparator are appropriate. Matched single chunks isolate the steering effect; rollouts measure the consequence after histories diverge. These answer different questions and should remain separate.

Zero unsafe executed points can be achieved by refusing the first chunk. Conversely, low goal error computed only for completed runs can conceal widespread rejection. “Completed” can also mean exhausting a rollout horizon without reaching the task goal unless those events are explicitly distinguished.

**Minimal change:** make the compact primary result joint: pre-acceptance execution-portion violation rate, stopped/numerically failed rollout counts, and goal-reaching completion rate over every attempted rollout. Retain final or last-accepted goal error for failures, with their failure labels. Show whole-chunk/unused-tail violations separately. Report jumps, intervention and runtime as costs. A successful safety result needs improved generation/acceptance together with useful progress; a tradeoff or failed adaptation remains reportable. No additional controller or comparison family is needed.

### 6. Medium — Reproducibility needs the sampler and paired inputs, not only the checkpoint

**Affected:** §4, line 68; §7, lines 136–140; supporting project README says generated artifacts are ignored by default.

The preservation list is sound. Seeds alone may not reproduce paired sources after stopping or diverging histories if random-number consumption depends on control flow. A best-validation checkpoint is also ambiguous without its selection rule, split and preprocessing. Ignored artifacts can be locally preserved but absent from a Git commit.

**Minimal change:** preserve a manifest linking model/data provenance and hashes to the frozen baseline commit, exact initial histories, scenario definitions, integration configuration and outputs. Index random sources by scenario/rollout/replanning index, or save the actual source draws, so earlier failure does not shift later pairings. Preserve unsuccessful attempts and machine-readable failure labels. Keep raw datasets/checkpoints outside Git as already intended, but record their locations and hashes; retain a small command/configuration description and final metrics with the report. No remote publication is necessary.

## What is not a methodology blocker

The current scope need not add whole-trajectory generation, hard endpoints, SRFMP, a learned dynamics model, arc constraints, a goal CLF, more LASA families or a physical robot. One training run and a small fixed evaluation suite can support an explicitly limited case study. The expanded-cap identity, exact-center warning, failure accounting and restrictions on application claims are already correctly stated.

The outstanding blocker to **claiming completed feasibility** is absence of evidence, not a demonstrated impossibility of the method. Applicant review should approve the method and its bounded failure outcome before specification/tickets proceed; this review authorizes no implementation.
