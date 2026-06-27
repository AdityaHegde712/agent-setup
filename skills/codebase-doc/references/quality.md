# Quality Checklist

Run this checklist before finalizing `CODEBASE.md`. Fix any "fail" before saving.

---

## Content quality

| Check | Pass criteria |
|---|---|
| Header one-liner is a capability statement | Describes what the system *does*, not what it *is* |
| No section mirrors the directory tree | No bullet list of file paths that adds no meaning |
| Every file path mentioned is load-bearing | Paths appear only when they are non-obvious or stable |
| Non-obvious patterns section has ≥3 entries | Or section is replaced by §12 if the project has no surprises |
| No filler sentences | No "this project uses modern best practices" or equivalent |
| Mermaid diagram has ≤12 nodes | Collapse if over limit |
| Tech stack table has a Notes column with real content | Not just framework names — at least some cells have constraints |
| CODEBASE.md does not duplicate README.md | Spot-check first three paragraphs of each |
| Development workflow commands are copy-pasteable | Tested mentally against what the shell commands would actually do |
| Glossary entries (if present) are genuinely ambiguous terms | Not standard English words |

---

## Staleness risk

Flag these in your report to the user — they need human review when the codebase changes:

| Risk item | Why it goes stale |
|---|---|
| File paths in key modules table | Files get renamed or refactored |
| DB table names in data layer | Migrations rename tables |
| Port numbers and commands | Config drift |
| Service names in monorepo map | Packages get added or removed |
| CI pipeline file names | Workflows get renamed |

---

## Length calibration

| Project size | Target length |
|---|---|
| Library / CLI / small project (<20 files) | 100–200 lines |
| Single-service backend / frontend app | 200–350 lines |
| Multi-service or full-stack | 300–500 lines |
| Monorepo with 3+ services | 400–600 lines + linked sub-docs |

If the draft exceeds the upper bound for its size tier, cut from these sections first
(in order): Glossary, Architecture decisions, Things to know before changing code.
Never cut Non-obvious patterns or Tech stack.

---

## Agent-readiness checks

These matter specifically for AI agents consuming this file:

| Check | Rationale |
|---|---|
| Non-obvious patterns are self-contained | Each entry makes sense without reading surrounding entries |
| No "see above" or "as mentioned" cross-references | Agents may load sections out of order |
| Commands include all flags needed to actually run | Agents run commands literally |
| Warnings are explicit, not implied | "Do not write to audit_log" not "audit_log is managed elsewhere" |
| Version numbers appear where they affect behavior | "Pydantic v2" not just "Pydantic" |

---

## Final gate

Before writing the file, answer these three questions:

1. **Would a competent developer reading this file produce better code than one
   who only read the source?** If no, the file needs more non-obvious content.

2. **Would an AI agent reading this file make fewer mistakes than one with only
   file-reading tools?** If no, the non-obvious patterns section needs work.

3. **Is every sentence here something that would be painful to discover by reading
   the code?** If not, cut it.

If all three answers are yes, ship the file.
