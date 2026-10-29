# Standalone methodology reviews

29 October 2026. Three agents were dispatched with **no inherited conversation history**, independent tasks and the same consolidated methodology. They reviewed the original body at Git commit `c300c67`, lines 1–154. Reports are analytic/document reviews, not experiments or implementation approval. No specification or tickets were created.

## Overall assessment

The reviews found **no fundamental mathematical or method-fidelity reason to reject the selected two-phase study**. The practicality verdict is conditional: small-scale feasibility is plausible, but training success, robust numerical recovery, useful detours and completion within the remaining time have not been demonstrated. A useful negative or incomplete result is possible. The original 18-hour ceiling and application headroom still apply.

| Review | Verdict | Main findings |
| --- | --- | --- |
| [Mathematics](mathematics.md) | Qualified mathematical pass | Barrier sign, tangent gradient, minimum-norm correction and separation across positions are correct. Near-center corrections can diverge; the singular schedule supplies no automatic finite-step certificate; filtering can stall. Includes an analytic finite-time margin bound under exact-flow/feasibility assumptions. |
| [RFMP fidelity](rfmp_fidelity.md) | Conditionally sound | Original-paper chunk/history/prior/training structure is preserved. Explicitly resolve horizon indexing, history pairing, state-dependent network inputs and Gaussian covariance conventions before a later implementation. |
| [Practicality and evaluation](practicality.md) | Coherent feasibility study; success unproven | Require a useful nominal rollout baseline; treat margin/grid/cutoff and near-center failure as one numerical problem; preserve source pairing; judge avoidance alongside goal progress and failures. |

## Changes made after review

Only factual clarifications and risk/validation explanations were incorporated into [methodology.md](../../methodology.md):

- The original horizon equations/prose disagree about inclusive counts; 8/4 array lengths are not verified author-code facts.
- Context uses the original paired-history range and is held fixed during each generation solve. Rollout history must not consult future demonstration positions.
- The prior's `σI` convention and the paper's incomplete MLP input prose are explicit reproduction gaps.
- Near-center ill-conditioning, possible stalls and the need to validate nominal rollouts are explicit.
- Goal-reaching, stopped failures, unsafe proposals and whole-chunk violations remain separate outcomes; pairing must survive earlier stopping.

These edits **do not select numerical defaults, change the prior, add a planner, alter the failure policy or expand scope**. Report line numbers refer to `c300c67`, not the subsequently clarified file. Reviewer recommendations about later operational choices are still recommendations.

## Applicant review focus

Read [the consolidated methodology](../../methodology.md) first. The material questions are whether the stated limited evidence is worthwhile, whether the remaining numerical risks are acceptable as an empirical study, and whether the disclosed RFMP reproduction gaps and phase gate match the intended project. The detailed reports explain those tradeoffs; successful experiments are not promised by any reviewer.

**Current gate: applicant methodology review.** Specification, tickets, tests, implementation, dataset preparation, training and experiments remain on hold. No new approval question or implementation action is implied by this review summary.

## Follow-up: audit of manifold language against code

At the applicant's request, a subsequent [implementation-level audit](manifold_implementation_audit.md) inspects the geometric-CBF controller/dynamics chain and compares its mechanical geometry with our first-order sampler. A separate [official RFM source audit](rfm_implementation_geometry.md) verifies projections, geodesic/JVP targets, metric loss and integration flags. The methodology now makes its existing round/product geometry explicit. The original three reports' line references remain tied to `c300c67`; the follow-up does not authorize any specification or implementation.

## Follow-up: user-proposed SO(3)/SO(2) lift

The [independent quotient-lift review](quotient_lift_independent.md) verifies the applicant's barrier differential, normalized-metric gradient, body-coordinate projection, horizontal nominal lift and exact projected exponential-Euler identity. The key correction is terminology: horizontal zero instantaneous axial spin is not global zero roll; holonomy and the lack of a global smooth frame section must be acknowledged. Metric changes and unsafe-center degeneracy retain their existing caveats. The audited representation is recorded in the core method for applicant review; it does not automatically change the approved S² learning task or authorize specs/tickets/implementation.
