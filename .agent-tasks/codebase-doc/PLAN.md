# Scope of CODEBASE.md Documentation Updates

Map recent architectural changes and configurations to CODEBASE.md.

## Core Scope:
1. **Tech Stack & Key Modules**:
   * Add `ua/` (Python/Pipenv/uv user-agent customizations backend).
   * Add new custom skills under `skills/`: `caveman`, `jupytext-notebooks`, `terraform-test-writer`.
   * Add `plugins/compaction-backup.js` as an active runtime hook.
2. **Non-Obvious Patterns**:
   * Document TDD Workflow and lockdown: exclusive test edit access for `@tester` only; developer agents blocked from test folders.
   * Document compaction backup plugin logic: capturing compaction summaries and transforming chat contexts with rolling episodic memories.
3. **Glossary & References**:
   * Add context reference docs like `agents/docs/tdd_workflow_agents_reference.md`.
