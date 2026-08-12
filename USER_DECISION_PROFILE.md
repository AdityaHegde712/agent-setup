# User Decision Profile & Confidence Matrix

## Confidence Scores

- **Architect Alignment**: 49
- **Orchestrator Alignment**: 30

## Execution Policy

- **Low Confidence (< 50%)**: "Conservative Mode" â€” Every major decision and tool invocation requires explicit user approval.
- **Medium Confidence (50-90%)**: "Predictive Mode" â€” Propose an action based on an assumed preference. If the user doesn't object to the specific assumption, proceed.
- **High Confidence (> 90%)**: "Autonomous Mode" â€” Execute based on established patterns and summarize assumptions.
  - **Exception**: Shell commands still require confirmation until score > 95.
  - **Hard Restriction**: `rm` commands and directory deletions ALWAYS require explicit user approval, regardless of score.

---

## General Development Heuristics

### 1. System Design & Architecture

- **Directory Organization**: Research outputs and artifacts belong in designated subdirectories (e.g., `.agent-tasks/<topic>/` or `_internal/`), not the project root. The root should contain only essential reference/blueprint documents.
- **Simplicity & Frameworks**: Prefer minimal viable solutions. Use standard frameworks (React, Vite, Conda, etc.) only when codebase is expected to exceed 500 lines of total code; prefer raw vanilla code/scripts for smaller sizes.
- **Foundation Finality**: Once a core architectural/foundational module passes development, adapt it via layers/bridges/shims rather than proposing rebuilds for downstream issues, unless exhaustively proven unsolvable.
- **Reference Grounding & Authority**: Treat user-provided domain specs as authoritative. Cite published sources, established libraries, or known design patterns for all architectural/methodological claims; avoid inventing novel mechanisms ad-hoc.
- **Interaction-First Architecture**: Always present multi-component systems by detailing their interaction/feedback loops first, rather than starting with static component inventories.
- **Explicit Scope & Determinism**: Clearly articulate in-scope vs. out-of-scope boundaries with rationale. Resolve all implementation options to a single concrete path before seeking approval.
- **Scale Stratification & Offloading**: Stratify models/modules per scale range when system behavior scales nonlinearly. Offload resource-intensive workloads (e.g., deep learning training) to external environments (e.g., Colab, cloud VMs) rather than running locally.
- **Independent Artifacts**: Ensure research prototypes and code artifacts are self-contained and reproducible without dependencies on private or environment-specific toolchains.
- **Diagram Formats**: Prefer Excalidraw JSON over draw.io XML for diagramming, as JSON is more easily edited and parsed by agents.
- **Deterministic LLM Output**: Prefer delimiter-friendly plaintext LLM output (section headers, `##` labels, separator lines) parsed via deterministic string manipulation over JSON/SSE retry chains. Unparseable output is a FATAL, phase-named error â€” never silently re-parse or fall back.
- **Single-Pass Pipelines**: Use one LLM call per generation pipeline; avoid streaming (SSE) and multi-call retry chains unless the use case demands them.
- **Stable-Key Resolution over Names**: When LLM output may rename/paraphrase entities (e.g., for JD suitability), anchor references to a source-stable key (numbered index from the input catalog) via a side map file; fuzzy name matching is defense-in-depth only.
- **Prompt Token Hygiene**: Keep URLs and large reference data out of prompts; resolve them through side lookup files to avoid token waste.
- **Phase Failure Semantics**: Distinguish fatal vs non-fatal pipeline phases. Non-fatal phases (e.g., PDF compile) persist artifacts and surface a flag (e.g., `pdf_error`) instead of aborting the run.
- **Windows Subprocess Calls**: Never use `asyncio.create_subprocess_exec` on Windows (ProactorEventLoop `NotImplementedError`); run blocking subprocesses via `subprocess.run` inside `asyncio.to_thread`.
- **Tool Path Resolution Chains**: Resolve external tool binaries via env var â†’ known default install path â†’ PATH fallback.

### 2. Operations & TDD Execution

- **Surgical Modifications**: Favor surgical, minimal diffs over wide-scale refactoring of surrounding code unless explicitly requested.
- **Utility Discovery & Minimal Dependencies**: Favor reusing existing project utilities over writing new ad-hoc scripts. Prefer the language standard library (e.g., Python stdlib) for simple utilities to maintain a zero-dependency footprint.
- **TDD & Permission Boundaries**: Follow strict TDD: batch-write locked test assertions first, verify they fail, then implement. Keep tests as an immutable contract; implementation agents run but must not modify tests (test-writing agents must not refactor implementation).
- **Write Tool Integrity**: If a file write/edit tool fails due to permissions or any other error, never attempt to bypass this by writing or modifying files via shell/terminal commands (e.g., `echo`, `cat`, or redirects). Instead, immediately report the failure to the user for resolution.
- **Git & Documentation Lifecycle**: Documentation updates and git commits must be batch-performed at the end of every project phase (referring to the Phases defined in the Architect's plan) rather than continuously throughout.
- **Sub-Agent Context & Execution**: Planning-only agents must not edit code; they delegate to orchestrators/executors. When invoking sub-agents, explicitly pass absolute paths and working directories to avoid context drift.
- **Branch Merging & Pull Requests**: Never handle branch merges locally and never initiate pull requests via agents. Instead, direct the user on which branch to merge into which, specify if rebases are necessary, and wait for the user to complete the merge manually.
- **Permanent Resurfacing Fixes**: If an issue would recur upon rebuilding or re-creation, implement a permanent code fix rather than skipping or patching it temporarily.
- **API Provider Integrations**: Always include an integration/connectivity validation script when adding or changing external API providers.
- **Bulk File Assessment via Technical Writer**: When the orchestrator needs to read many files for assessment without context bloat, delegate the reading task to `app/technical-writer` rather than reading files directly.
- **Prompt-Map-Driven Sub-Agent Design**: When invoking `@util/sub-agent-creator`, reference `~/.config/opencode/system_prompts_map.json` and require it to search tags for vetted system-prompt subsections before writing manifests. Provide a permissions template so manifests are generated correctly: `bash: deny` (not `bash: false`), `edit: deny`, `task: deny`, read scope limited to specific directories, steps limit set. Design provenance (which prompt-map tags were used, rationale) belongs in a separate `creation_summary.md` â€” never inside the agent manifests.
- **Frozen vs Mutable Tests**: Split contract tests (`tests/spec/`, frozen, define behavior) from integration tests (`tests/integration/`, mutable). Reuse a single golden fixture across modules that share a data format.
- **Live Owner-Owned Files**: The Owner edits authoritative files (prompts, configs, YAML maps) directly between turns. Always re-read/re-verify ground truth before finalizing plans or code that depends on them.
- **Planning-Only Sessions**: Keep architect/planning sessions free of implementation; the Owner launches execution in a separate session. Write plans and await approval â€” never begin implementation inside a planning session.
- **Mandatory Reduced-Size E2E Smoke for Multi-Hour Operations**: Any multi-hour operation (data prep, data generation, model training) MUST complete a full end-to-end reduced-size smoke test (same pipeline, `--limit N` / reduced epochs / small subset through every stage to final artifact) BEFORE the full run is launched. The full run may only launch after the smoke produces a verified, valid final artifact and is approved by the Owner. Rationale: 2026-08-07 T2.2 full run burned 4 h at jobs=4 with ZERO output because the jobs>1 worker path (pickled df slices) had never been smoke-tested end-to-end in its full-run configuration; the earlier jobs=1 smoke did not cover it.

### 3. Local UI, WebViews & Web Compatibility

- **Mobile File Compatibility**: Use a single self-contained HTML file for WebViews launched via local file managers (using `content://` or `file://` URIs) to prevent relative path breakage.
- **Asynchronous CDN Loading**: Dynamically inject external library scripts to ensure page load is not blocked if CDNs fail or respond slowly.
- **IndexedDB for Handles**: Persist structured-cloneable objects (like file handles) in IndexedDB, as localStorage cannot store them.
- **Form Button Types**: Explicitly set `type="button"` on all non-submit `<button>` tags within a `<form>` to prevent accidental submission.
- **Responsive Layouts**: Prefer card-based or label-value layouts over fixed-width tables for viewports ~360px wide to avoid horizontal overflow.

### 4. CLI & Automation Tools

- **CLI Input Filtering**: Warn about and skip unsupported inputs/URLs rather than silently ignoring or throwing fatal errors.
- **Paced Batch Operations**: Implement paced batching (`--batch-size N`) with interactive confirmation pauses and support for clean exits (e.g., Ctrl+C) when triggering external batch processes.

### 5. Code & Documentation Standards

- **Error Handling**: Raise exceptions early and loudly. Avoid soft-failure or silent fallback mechanisms that create illusions of functionality.
- **Third-Party Libraries**: For minor features, prefer using a popular third-party micro-package (e.g., lodash, date-fns) as the first choice. Write a custom implementation only if the package does not fit the target task.
- **In-Code Documentation**: Concise, type-hinted, and modular. Use Google-style docstrings/JSDoc.
- **Plans/Design**: High granularity, technical detail, mathematical/mechanistic precision, and explicit failure-mode analysis over qualitative descriptions.
- **Reference Paths in Reports**: Reports and summary documents must include explicit file paths to source data so the next reader or agent can navigate directly without searching.
- **Post-Reorganization Reference Audit**: After any file move, rename, or delete operation, audit all documentation that references old paths and update them to match the new layout.
- **LLM Text Escaping**: All LLM-derived text must be escaped before embedding into templates/output formats; the LLM never authors markup or commands.
- **API Contract Normalization**: Normalize API response payloads to a fixed snake_case key contract; surface non-fatal phase flags as explicit fields.

### 6. Plan Version Labeling & Phasing

- **Version Hygiene**: When adding new features to an already-approved plan, do NOT bump the entire plan version. Instead, keep the approved plan at its current version and add new sections explicitly marked as "vNext Proposed Additions" or similar. Each version label tracks what was approved at each decision point, not a cumulative version number.
- **Feature Classification**: Label every distinct set of features with its intended release version (e.g., "v1.0 feature" vs "planned for v1.1"). Deferred/later features get their own section in the plan, not merged into the current version's sections.

---

## Workspace Preferences

- **Theme**: Dark themes preferred by default for most tools (e.g., `#121212` backgrounds, `#e0e0e0` text).
- **Test Placement**: Dedicated isolated test directories (e.g., `tests/` at the root/top-level) are strictly preferred over co-locating test files with source code.
- **Formatting & Linting**: Auto-formatters/linters (e.g., Prettier, Black, Ruff, ESLint) must be run automatically on modified files before committing.
- **Git Commits**: Milestone-based auto-commits are preferred.
- **Root Cleanliness**: Keep the project root limited to essential reference/blueprint documents only. Move research artifacts, raw data, and debug scripts to designated subdirectories.
- **Per-Dataset Raw/Processed Split**: Use `data/<dataset>/raw/` for original downloads and `data/<dataset>/processed/` for derivatives. Maintain a `DATASET_SUMMARY.md` per dataset documenting schema, stats, and quality notes.
- **Research Artifact Disposability**: Raw API search results (JSON), throwaway debug scripts (<40 lines), and stale session logs can be deleted once their findings are captured in structured reports.
- **Frontend Style (web apps)**: No Bootstrap. Component libraries welcome â€” prefer fixed/token-based style themes over hand-rolled CSS. Preferred tier: Mantine, shadcn/ui, Ant Design. Acceptable tier: MUI, HeroUI. Dark minimal flat UI with hairline dividers preferred.
- **Archived Context Hygiene**: Archived legacy artifacts (e.g., `.agent-tasks/archived/`, `old_code.rar`) stay unread unless explicitly requested; do not surface their content into working context.


