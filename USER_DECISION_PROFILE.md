# User Decision Profile & Confidence Matrix

## Confidence Scores

- **Architect Alignment**: 52
- **Orchestrator Alignment**: 33

## Execution Policy

- **Low Confidence (< 50%)**: "Conservative Mode" — Every major decision and tool invocation requires explicit user approval.
- **Medium Confidence (50-90%)**: "Predictive Mode" — Propose an action based on an assumed preference. If the user doesn't object to the specific assumption, proceed.
- **High Confidence (> 90%)**: "Autonomous Mode" — Execute based on established patterns and summarize assumptions.
  - **Exception**: Shell commands still require confirmation until score > 95.
  - **Hard Restriction**: `rm` commands and directory deletions ALWAYS require explicit user approval, regardless of score.

---

## General Development Heuristics

### 1. System Design & Architecture

- **Simplicity & Frameworks**: Prefer minimal viable solutions. Use standard frameworks (React, Vite, Conda, etc.) only when codebase is expected to exceed 500 lines of total code; prefer raw vanilla code/scripts for smaller sizes.
- **Foundation Finality**: Once a core architectural/foundational module passes development, adapt it via layers/bridges/shims rather than proposing rebuilds for downstream issues, unless exhaustively proven unsolvable.
- **Reference Grounding & Authority**: Treat user-provided domain specs as authoritative. Cite published sources, established libraries, or known design patterns for all architectural/methodological claims; avoid inventing novel mechanisms ad-hoc.
- **Interaction-First Architecture**: Always present multi-component systems by detailing their interaction/feedback loops first, rather than starting with static component inventories.
- **Explicit Scope & Determinism**: Clearly articulate in-scope vs. out-of-scope boundaries with rationale. Resolve all implementation options to a single concrete path before seeking approval.
- **Scale Stratification & Offloading**: Stratify models/modules per scale range when system behavior scales nonlinearly. Offload resource-intensive workloads (e.g., deep learning training) to external environments (e.g., Colab, cloud VMs) rather than running locally.
- **Independent Artifacts**: Ensure research prototypes and code artifacts are self-contained and reproducible without dependencies on private or environment-specific toolchains.
- **Diagram Formats**: Prefer Excalidraw JSON over draw.io XML for diagramming, as JSON is more easily edited and parsed by agents.

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

### 6. Plan Version Labeling & Phasing

- **Version Hygiene**: When adding new features to an already-approved plan, do NOT bump the entire plan version. Instead, keep the approved plan at its current version and add new sections explicitly marked as "vNext Proposed Additions" or similar. Each version label tracks what was approved at each decision point, not a cumulative version number.
- **Feature Classification**: Label every distinct set of features with its intended release version (e.g., "v1.0 feature" vs "planned for v1.1"). Deferred/later features get their own section in the plan, not merged into the current version's sections.

---

## Workspace Preferences

- **Theme**: Dark themes preferred by default for most tools (e.g., `#121212` backgrounds, `#e0e0e0` text).
- **Test Placement**: Dedicated isolated test directories (e.g., `tests/` at the root/top-level) are strictly preferred over co-locating test files with source code.
- **Formatting & Linting**: Auto-formatters/linters (e.g., Prettier, Black, Ruff, ESLint) must be run automatically on modified files before committing.
- **Git Commits**: Milestone-based auto-commits are preferred.

