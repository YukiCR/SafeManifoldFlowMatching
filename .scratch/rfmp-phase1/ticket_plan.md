# Proposed Phase 1 ticket breakdown

**Status: approved — applicant accepted granularity, blocking edges, test interfaces and local setup on 29 October 2026.** One local Markdown issue per ticket is published below.

Source: [Phase 1 specification draft](spec.md). No Phase 2 implementation is included. Work the unblocked frontier; use red-before-green at the agreed interfaces.

1. **Generate an analytically checkable sphere chunk.** Blocked by: none. Delivers the public sphere geometry interface and a generation path/sampler that reproduces independently known great-circle motion, stays on the product sphere and reports unsupported inputs. This validates geometry through an observable generated sequence. Test data are analytical fixtures, not synthetic project training demonstrations. Proposed time cap: 1 hour.
2. **Learn and sample the real LShape conditional chunks.** Blocked by: 01; real official MAT file. Delivers source provenance, resampling/embedding, declared window split and paired history, training loss/EMA selection, and a trained chunk-generation result through the public Phase 1 study interface. Includes a bounded smoke run and then the declared 200-epoch fit. Proposed time cap: 2 hours; missing data remains an explicit blocker.
3. **Reproduce complete motion by autonomous replanning.** Blocked by: 02. Delivers the 35-run seeded study, generated-history conditioning, correct final partial execution and all declared fidelity/goal/geometry diagnostics. Applies the specified Phase 1 freeze gate and preserves failed attempts. Proposed time cap: 1 hour.
4. **Freeze and explain the validated baseline.** Blocked by: 03. Delivers the immutable configuration/split/checkpoint manifest, baseline Git reference, reproducible commands, sphere visualization and concise results/limitations. If validation failed, delivers the failure report and leaves Phase 2 blocked instead of creating a success claim. Proposed time cap: 1 hour including the earlier workflow overhead.

Only immediate blockers are listed; transitive dependencies are not repeated. No mechanical refactor or independent safety ticket is needed in this empty project.

## Test interfaces proposed for agreement

- **Sphere geometry:** public geometric operations/path behavior with independent analytical expected values.
- **Phase 1 study:** preparation, fit, generate, rollout and evaluation behavior; internal layers/helpers are not separate test interfaces.

## Workflow setup draft for approval

The applicant selected local Markdown and the default statuses. Proposed local configuration:

The [exact setup draft](../../docs/agents/setup_draft.md) shows the proposed documents and AGENTS addition before applying them.

- Issue tracker: specs at `.scratch/<feature>/spec.md`, tickets one per `.scratch/<feature>/issues/NN-title.md`, blocking edges listed in each ticket.
- Status vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`.
- Domain layout: one root context document and optional ADRs, created only as needed; use the method's established domain terms. No monorepo layout or remote issue publication.
- Add an `Agent skills` section to the existing project AGENTS, linking tracker, triage-label and domain consumer-rule documents. Preserve all surrounding applicant decisions.

Approval of this concrete plan confirms the setup draft, ticket granularity/edges and these two test interfaces. It does not authorize Phase 2. After approval, publish one local issue per ticket, mark its actual status and begin TDD on ticket 01.
