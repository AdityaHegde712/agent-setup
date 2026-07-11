# Opencode Setup & Agent Roster

My personal setup for OpenCode, detailing the agent hierarchy, specialized skills, custom commands, and modular configuration.

---

## 🏗️ Global Agent Roster

The environment follows a modular, hierarchical structure where **Primary Agents** coordinate a specialized roster of **Sub-agents**.

### 1. Primary Agents (The Core Team)

- **`orchestrator`**: The Project Manager. Translates blueprints into tasks, delegates to sub-agents, and maintains the `PROJECT_STATUS.md`.
- **`architect`**: The Lead Designer. Focuses on Clean Architecture and Uncle Bob's principles. Produces sequential implementation plans.
- **`codebase-analyst`**: The Onboarding Lead. Specialized in mapping existing codebases and coordinating documentation (`CODEBASE.md`).
- **`doc-oracle`**: The Research & Mirroring Specialist. Deep-dives into OpenCode and Claude Code docs to mirror "Gold Standard" best practices.
- **`debugger`**: The Diagnosis & Fix Specialist. Diagnoses bugs, proposes fixes using the `code-debugger` skill, and drafts delegation plans.
- **`interruption-handler`**: The Checkpoint Manager. Handles session interruptions, audits workspace state, and documents next steps in `resume_here.md`.

### 2. Specialized Sub-agents (Execution Layers)

| Layer    | Agent                                                                                                                                                                                                   | Key Responsibilities                                                                                                        |
| :------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :-------------------------------------------------------------------------------------------------------------------------- |
| **App**  | `backend-dev`, `frontend-dev`, `tester`, `ops-expert`, `technical-writer`                                                                                                                               | Full-stack application development, testing, and documentation.                                                             |
| **ML**   | `data-engineer`, `model-scientist`                                                                                                                                                                      | Data pipelines, ETL, model training, and evaluation.                                                                        |
| **Util** | `clean-coder`, `research-analyst`, `security-reviewer`, `general-builder`, `skill-creator`, `skill-tester`, `structure-expert`, `theory-deep-dive`, `codebase-doc`, `doc-analyzer`, `sub-agent-creator` | Specialized utilities for code quality, SOTA research, skill building, documentation mapping, and dynamic agent generation. |

---

## 🛠️ Global Skills

A collection of native OpenCode skills providing advanced capabilities across data, design, literature, and automation.

| Category         | Skill                         | Key Capabilities                                                                           |
| :--------------- | :---------------------------- | :----------------------------------------------------------------------------------------- |
| **Data & ML**    | `ml-data-import`              | Load, inspect, and prepare data files (CSV, Parquet, JSON, SQLite, etc.) for ML workflows. |
|                  | `xlsx`                        | Excel spreadsheet manipulation (.xlsx, .csv, .tsv) with formula recalculation.             |
|                  | `pdf`                         | PDF creation, merging, splitting, text extraction, and OCR.                                |
|                  | `docx`                        | Word document (.docx) generation, editing, and content extraction.                         |
| **Development**  | `mcp-builder`                 | Building Model Context Protocol (MCP) servers in Node.js and Python.                       |
|                  | `webapp-testing`              | Playwright-based testing and UI verification of local web apps.                            |
|                  | `code-debugger`               | Diagnostic processes and debugging workflows for web/desktop apps.                         |
|                  | `github-workflows`            | Personal conventions for Git operations and GitHub workflows.                              |
|                  | `jupytext-notebooks`          | Read and write Jupyter Notebooks (`.ipynb`) natively in sync with Markdown/Python.          |
|                  | `terraform-test-writer`        | Generate Terraform unit and integration test suites using Go/Terratest.                    |
| **Design & UI**  | `frontend-design`             | Responsive, high-quality, production-ready frontend interfaces.                            |
|                  | `canvas-design`               | Original visual art and layout designs in PNG and PDF.                                     |
|                  | `theme-factory`               | Custom styling for reports, HTML, and documents using themes.                              |
|                  | `brand-guidelines`            | Brand compliance using Anthropic's colors and typography.                                  |
| **Productivity** | `internal-comms`              | Formatting templates for internal reports, status updates, and FAQs.                       |
|                  | `slack-gif-creator`           | Generating animated GIFs optimized for Slack.                                              |
|                  | `task-paralysis-break`        | Decision fatigue mitigation and task prioritization.                                       |
|                  | `anxiety-rationalizer`        | Processing attachment anxiety with objective reality checks.                               |
|                  | `codebase-doc`                | Generation of comprehensive global codebase documentation.                                 |
|                  | `caveman`                     | Ultra-compressed, terse communication style for low-token developer coordination.          |
| **Literature**   | `literature-search-arxiv`     | arXiv publication search and document retrieval.                                           |
|                  | `literature-search-biorxiv`   | BioRxiv/medRxiv preprint browsing and download.                                            |
|                  | `literature-search-europepmc` | Open-access PMC article search and full-text retrieval.                                    |
|                  | `literature-search-openalex`  | OpenAlex database querying for citation and author bibliometrics.                          |
|                  | `pubmed-database`             | Querying medical literature, clinical trials, and compound/gene links.                     |
|                  | `science-skills-common`       | Shared helper libraries (e.g. rate-limiting HTTP clients) for science tools.               |

---

## ⚡ Custom Commands (Slash Commands)

Bespoke shortcuts mapped directly into the system to trigger predefined behaviors:

- **`/anxious`**: Ground catastrophizing and anxious thoughts in relationship patterns.
- **`/goal`**: Extra-thorough, long-running agent execution targeting comprehensive objectives.
- **`/goodnight`**: Archiving the current session state, compiling task completions.
- **`/grill-me`**: Interactive alignment interview to resolve design decisions.
- **`/initialize`**: Bootstrapping new project structures and configurations.
- **`/learn`**: Persisting developer rules and learning feedback for future tasks.
- **`/literature-survey`**: Automating literature searching, downloading, and synthesis.
- **`/rmslop`**: Cleans up workspace artifacts, caches, and temporary files.
- **`/spellcheck`**: Text/spelling analysis and correction.
- **`/task-paralysis`**: Mitigating decision paralysis and prioritizing tasks.

---

## 📂 Additional Setup Components

Beyond agents and skills, this configuration contains several supporting directories:

- **`plugins/`**: Custom runtime modules (e.g., `bedtime-reminder.js` for schedule alerts, and `compaction-backup.js` for rolling episodic memory backup).
- **`scripts/`**: Practical utility scripts (e.g., `html_to_md.py` for content parsing, `tex_to_md.py` for LaTeX-to-Markdown conversion, and workspace initializers).
- **`themes/`**: JSON colorschemes to design premium documents and user interfaces (e.g., `charcoal.json`, `smoke-theme.json`).
- **`ua/`**: Python-based customizations backend managing state and exposing capabilities through MCP.

---

## 🚀 Personal Setup & Roadmap

### Upcoming Features

- **Skills to Implement**:
  - **FFmpeg Executor**: Video and audio processing command utilities.
  - **Canvas Scraper**: Academic content retrieval and scraping from Canvas LMS.
  - **Database Integration (`sqlite-postgres`)**: CRUD operations, schema creation, and database connection handlers.
- **Specialized Agents**:
  - **Homework Agent**:
    - `canvas` _(sub-agent)_: Automates scraping Canvas LMS using tools/skills to download assignments.
    - `builder` _(sub-agent)_: Automated coding and solution development based on assignment details.
    - `validator` _(sub-agent)_: Validates the builder agent outputs against assignment instructions.

---

## 📂 File System Standards

- **Agent Definitions**: Stored as `.md` files with YAML frontmatter.
- **Task Logging**: Every agent maintains logs in `.agent-tasks/<agent-name>/` (`PLAN.md`, `TASKS.md`, `STATUS.md`).
- **User Alignment**: Agents read `~/.config/opencode/USER_DECISION_PROFILE.md` to adapt to user heuristics.
- **TDD & Test Lockdown**: Agent-facing Test-Driven Development (TDD) execution loops are documented in [tdd_workflow_agents_reference.md](file:///c:/Users/hifia/Projects/opencode-setup/agents/docs/tdd_workflow_agents_reference.md). Developer agents are restricted from editing test files (`tests/**/*: deny`), leaving `@tester` with exclusive test suite write access.
