# Next Session — Handoff Notes

## Branch

`feature/add-tdd-workflow-and-test-permissions`

## Accomplishments This Session

1. **TDD workflow integration** — Added TDD (Red-Green-Refactor) instructions to all agent workflows referencing `agents/docs/ttd_workflow_agents_reference.md`. Locked down test directory permissions for developer agents. Only Tester has write access to tests.
2. **Permission hardening** — All agents changed from blanket `edit: allow` to granular permissions. Dev agents: `tests/**/*: deny`. Tester: exclusive test access. doc-oracle: log-file only.
3. **Decision profile update** — Added 6 new heuristics (reference grounding, interaction dynamics primacy, explicit scope boundaries, proactive trade-off surfacing, information flow auditing) and bumped confidence scores.
4. **User-agent backend (`ua/`)** — Added a Python project with MCP integration and storage CRUD layer for personal opencode customizations.
5. **GitHousekeeping** — Fixed remote URL to `agent-setup.git`, added `.venv` to `.gitignore`.

## Commits Made

```
5afcbea chore: add .venv to gitignore
a45afed feat(ua): add user-agent customization backend for opencode
55bf1dc feat(agents): integrate TDD workflow with test permission lockdowns
```

## Next Steps / Context to Resume

- The `ua/` project source files are committed but `.venv/` was excluded (now in `.gitignore`).
- `package.json` and `package-lock.json` have CRLF-only diffs — not committed, verify if real changes exist.
- The branch is feature work on `main`-only repo. Consider opening a PR to `main` or merging when ready.
