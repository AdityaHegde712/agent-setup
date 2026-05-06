# OpenCode Agent Ecosystem: Context Blueprint

### 1. The Core Architecture
A modular, high-performance AI/ML development team configured in `~/.config/opencode/agents/` using **OpenCode Zen (Free Tier)** models.

*   **Primary (Leadership)**:
    *   **Architect**: High-level system design (Clean Architecture/Uncle Bob). Produces agent-tagged, sequentially phased plans.
    *   **Orchestrator**: Project manager. Manages the `PROJECT_STATUS.md` ledger and facilitates handoffs between specialized agents.
*   **Specialized Squads**:
    *   **ML**: `Data-Engineer` (ETL/Profiling), `Model-Scientist` (SOTA/Training).
    *   **App**: `Backend-Dev`, `Frontend-Dev`, `Tester`, `Ops-Expert` (AWS/Deployment), `Technical-Writer` (README/API Docs).
    *   **Utility**: `Clean-Coder` (Refactoring), `Research-Analyst` (Paradigms/R&D), `Security-Reviewer` (Vulnerability audits).

### 2. Operational Protocols
*   **"Owner" Definition**: Refers strictly to the human User.
*   **Plan Confirmation**: Every agent (primary or sub) MUST generate a `PLAN.md` and obtain Owner approval before editing files.
*   **Artifact Strategy**: Documentation is stored in `.agent-tasks/<agent-name>/` containing `PLAN.md`, `TASKS.md`, and `STATUS.md`.
*   **Manual Fallback**: If agents hit auth blocks or download limits, they notify the Orchestrator, who requests manual intervention from the Owner.

### 3. Custom Tool Suite (Global)
*   **`data_profiler`**: Generates stats for large datasets. Optimized for Parquet > 500MB using the `pyarrow` engine.
*   **`security_scanner`**: Scans workspace for hardcoded secrets, sensitive files (.env, .pem), and dangerous Python patterns.
*   **`experiment_log`**: Atomic JSON ledger for tracking model hyperparameters and metrics across runs.

### 4. Technical Constraints
*   **Clean Code**: Adherence to Uncle Bob’s principles, KISS, and modular, atomic function design.
*   **Documentation**: Google Style docstrings for all custom tool logic (Python).
*   **Models**: Optimized use of `big-pickle` (reasoning), `nemotron-3-super-free` (technical), and `minimax-m2.5-free` (logic).
