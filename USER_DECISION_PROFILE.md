# User Decision Profile & Confidence Matrix

## Confidence Scores
- **Architect Alignment**: 22
- **Orchestrator Alignment**: 20

## Execution Policy
- **Low Confidence (< 50%)**: "Conservative Mode" — Every major decision and tool invocation requires explicit user approval.
- **Medium Confidence (50-90%)**: "Predictive Mode" — Propose an action based on an assumed preference. If the user doesn't object to the specific assumption, proceed.
- **High Confidence (> 90%)**: "Autonomous Mode" — Execute based on established patterns and summarize assumptions. 
    - **Exception**: Shell commands still require confirmation until score > 95.
    - **Hard Restriction**: `rm` commands and directory deletions ALWAYS require explicit user approval, regardless of score.

## Decision Heuristics

### 1. Design & Architecture (Architect)
- **Integrative Excellence**: Performance and Maintainability are not trade-offs. Code must be high-performance, modular, and scalable simultaneously.
- **Evidence-Based Planning**: Always "Explore & Profile" the existing codebase/data before drafting a new architecture. Avoid code bloat by reusing existing utilities.
- **Granular Planning**: Architecture documents and plans must be comprehensive and explanatory, enabling a domain-newcomer to implement the feature without issues.

### 2. Operations & Execution (Orchestrator)
- **Tool Selection**: Favor existing project utilities discovered during the "Explore" phase over writing new ad-hoc scripts.
- **Safe Autonomy**: Strictly follow the Execution Policy. Never assume autonomy for destructive operations.

### 3. Documentation Standards (Global)
- **In-Code**: Concise, type-hinted, and modular. Use Google-style docstrings for Python logic.
- **Repository (README)**: Standard sections are sufficient; LLM-default templates are a good starting point.
- **Plans/Design**: High granularity and technical detail.

## Alignment Log
- [2026-05-08]: Initial profile created based on user interview. Base scores set to 20.
- [2026-05-10]: Design assignment plan approved by user. Architect Alignment +2.
