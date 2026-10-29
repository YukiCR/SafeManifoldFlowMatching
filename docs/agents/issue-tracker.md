# Issue tracker: Local Markdown

One feature per .scratch/<feature>/ directory. The specification is spec.md;
implementation tickets are issues/NN-title.md, numbered from 01 in dependency
order. Publish one file per approved ticket, never a combined issues file.
Each ticket records its Status, immediate Blocked by edges and acceptance criteria.
Append discussion under Comments. Fetch a ticket by reading that file.
Publishing means writing these local files; no GitHub issue creation is implied.

Keep triage Status separate from execution Progress. A ticket with Progress: completed is finished and skipped when selecting the frontier; its dependents can start when their remaining blockers are satisfied.
