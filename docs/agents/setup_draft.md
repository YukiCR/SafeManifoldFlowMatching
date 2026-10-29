# Local workflow setup — review draft

The applicant selected local Markdown and default triage statuses. These are the proposed exact configuration contents, to apply with the approved Phase 1 ticket/test-interface plan. No remote issues will be published.

## Proposed project AGENTS addition

```markdown
## Agent skills

### Issue tracker

Use local Markdown specs and one file per ticket under .scratch. See docs/agents/issue-tracker.md.

### Triage labels

Use the five default statuses. See docs/agents/triage-labels.md.

### Domain docs

Single-context project; consume existing context/ADRs when present. See docs/agents/domain.md.
```

## Proposed issue-tracker document

```markdown
# Issue tracker: Local Markdown

One feature per .scratch/<feature>/ directory. The specification is spec.md;
implementation tickets are issues/NN-title.md, numbered from 01 in dependency
order. Publish one file per approved ticket, never a combined issues file.
Each ticket records its Status, immediate Blocked by edges and acceptance criteria.
Append discussion under Comments. Fetch a ticket by reading that file.
Publishing means writing these local files; no GitHub issue creation is implied.
```

## Proposed triage-label document

```markdown
# Triage labels

| Role | Status |
| --- | --- |
| needs-triage | needs-triage |
| needs-info | needs-info |
| ready-for-agent | ready-for-agent |
| ready-for-human | ready-for-human |
| wontfix | wontfix |

Use needs-info while a prerequisite/decision is missing; use ready-for-agent
only for an approved, actionable ticket. Record actual progress and blockers.
```

## Proposed domain-consumer document

```markdown
# Domain docs

Single-context project. Read root CONTEXT.md if it exists, and relevant docs/adr
records before implementation. If absent, proceed silently; create them only
when domain terms or architectural decisions actually need recording.
Use the established methodology vocabulary: source recording, window/reference,
context, product-sphere chunk, generation time, execution portion, rollout and
baseline. Keep generation and physical rollout time distinct. Surface any ADR
conflict rather than silently replacing a decision.
```
