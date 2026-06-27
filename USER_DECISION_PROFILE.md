# User Decision Profile & Confidence Matrix

## Confidence Scores
- **Architect Alignment**: 46
- **Orchestrator Alignment**: 39

## Execution Policy
- **Low Confidence (< 50%)**: "Conservative Mode" — Every major decision and tool invocation requires explicit user approval.
- **Medium Confidence (50-90%)**: "Predictive Mode" — Propose an action based on an assumed preference. If the user doesn't object to the specific assumption, proceed.
- **High Confidence (> 90%)**: "Autonomous Mode" — Execute based on established patterns and summarize assumptions. 
    - **Exception**: Shell commands still require confirmation until score > 95.
    - **Hard Restriction**: `rm` commands and directory deletions ALWAYS require explicit user approval, regardless of score.

---

## General Development Heuristics

### 1. System Design & Architecture
- **Simplicity First**: Always prefer the simplest solution that gets the job done. Start with a minimal viable approach and only add complexity when justified by concrete requirements. Lead with the simplest option and tag complexity-adders as optional.
- **Framework Preference**: Prefer frameworks (e.g., React, Vue, Next.js, Vite, Conda/Poetry for environments) for applications that will exceed 500 lines of total code. For minuscule scripts or tools under 500 lines, raw vanilla code is preferred.
- **Foundation Finality**: Once a foundational module (e.g., storage adapter, data manager, core architecture) is approved and passes development, do not propose rebuilding or replacing it in response to downstream compatibility issues unless those issues are exhaustively verified as unsolvable within the existing architecture. Use adaptation layers, bridges, or shims first.
- **Domain Document Primacy**: Treat user-provided domain-specific reference documents (variables guides, domain papers, technical specs) as authoritative over generic best practices.
- **Separation of Modeling Scales**: When modeling physical systems where behavior scales nonlinearly with a parameter (e.g., size), stratified models or modules per scale range perform better than a single universal one.

### 2. Operations & Execution
- **Surgical Modifications**: Favor surgical, minimal diffs over wide-scale refactoring of surrounding code unless explicitly requested by the user.
- **Tool Selection**: Favor existing project utilities discovered during the "Explore" phase over writing new ad-hoc scripts.
- **Safe Autonomy**: Strictly follow the Execution Policy. Never assume autonomy for destructive operations.

### 3. Local WebViews & File Manager Contexts
- **Single-File Fallback**: When building web apps that might be opened directly from local mobile file managers (using `content://` URIs), use a single, self-contained HTML file because relative resource paths will break.
- **Dynamic Asset Loading**: Load external CDN libraries dynamically via script injection to avoid blocking if the CDN fails or is slow.
- **Handle Persistence**: Persist directory/file handles in IndexedDB (which supports structured clone of handles), as localStorage cannot store them.
- **Form Button Types**: Any `<button>` rendered inside a `<form>` must have an explicit `type="button"` unless it is the explicit submit button.
- **Mobile Table Layouts**: For displaying columns on mobile (screen width ~360px), a card-based layout (label-value rows) is much more reliable than fixed-width tables, which tend to overflow.

### 4. Infrastructure & Provider Preferences
- **Model Provider Flexibility**: If the primary model provider (e.g., OpenRouter) is unavailable or rate-limited, fall back to OpenCode Zen models. Use the mapping: coding agents → DeepSeek V4 Flash Free or Nemotron 3 Ultra Free, general agents → MiMo-V2.5 Free or Big Pickle.

### 5. Code & Documentation Standards
- **Error Handling**: Raise exceptions early and loudly. Avoid soft-failure or silent fallback mechanisms that create illusions of functionality.
- **Third-Party Libraries**: For minor features, prefer using a popular third-party micro-package (e.g., lodash, date-fns) as the first choice. Write a custom implementation only if the package does not fit the target task.
- **In-Code Documentation**: Concise, type-hinted, and modular. Use Google-style docstrings/JSDoc.
- **Plans/Design**: High granularity and technical detail.

---

### 6. Plan Version Labeling & Phasing
- **Version Hygiene**: When adding new features to an already-approved plan, do NOT bump the entire plan version. Instead, keep the approved plan at its current version and add new sections explicitly marked as "vNext Proposed Additions" or similar. Each version label tracks what was approved at each decision point, not a cumulative version number.
- **Feature Classification**: Label every distinct set of features with its intended release version (e.g., "v1.0 feature" vs "planned for v1.1"). Deferred/later features get their own section in the plan, not merged into the current version's sections.
- **PR Evaluation Delegation**: PR evaluation is high-context work. Never review PRs directly. Always delegate to `@util/research-analyst` with explicit criteria: what to evaluate, what alternatives to find, and what recommendation format to return.

### 7. Bookmark-Based Automation Tools
- **URL filtering**: Non-source links discovered in bookmarks folders should be **warned about but skipped**, not silently ignored nor processed.
- **Browser opening**: For tools that open search URLs in browser, the MVP should open all URLs directly; throttling/delay can be added later if needed.
- **Dependency philosophy**: For simple bookmark→search tools, prefer pure Python stdlib with zero external dependencies.
- **Batch processing**: When opening many browser tabs from CLI, use `--batch-size N` for paced opening with Enter-to-continue pauses. Show progress ("Opened X/total — Press Enter for next N"), support Ctrl+C clean exit during pause.

## Decision Log
- **2026-06-21**: ARVR project — AI-Powered AR Furniture Visualizer (Web PWA). Owner approved full plan without changes. Architecture: Vite + React + Three.js/WebXR + OpenAI GPT-4o-mini. 14-day MVP with static product catalog. Confidence increased from 48→50.
- **2026-06-26**: ResumePipeline Phase 4 (API) completed seamlessly — 20 endpoints, 27 tests. Confidence +2.
- **2026-06-26**: ResumePipeline Phase 5 (Frontend) completed with minor friction (sub-agent step limits). 50 files, 7 pages, 0 TS errors. Confidence -2.
- **2026-06-26**: ResumePipeline Phase 6 (security audit + README) completed.
- **2026-06-26**: Architect violated workflow — executed fix (5 frontend hooks destructure) instead of planning-only and handing off to Orchestrator. Alignment -6.
- **2026-06-26**: Phase 7 plan (generation crash, model hardcoding, auto-matching) approved without changes. Alignment +2.

## Workspace Preferences
- **Theme**: Dark themes preferred by default for most tools (e.g., `#121212` backgrounds, `#e0e0e0` text).
- **Test Placement**: Dedicated isolated test directories (e.g., `tests/` at the root/top-level) are strictly preferred over co-locating test files with source code.
- **Formatting & Linting**: Auto-formatters/linters (e.g., Prettier, Black, Ruff, ESLint) must be run automatically on modified files before committing.
- **Git Commits**: Milestone-based auto-commits are preferred.
- **Literature API Credentials**:
  - `NCBI_API_KEY`: a042b6045d3251170e09f2c305099e997107 (for 10 QPS PubMed limits)
  - `OPENALEX_EMAIL`: aditya.hegde@sjsu.edu (for OpenAlex polite pool access)
  - `OPENALEX_API_KEY`: oDOOwhwhUg2TRHYSkL8zdQ (for OpenAlex api access)
