---
description: Comprehensive overview and personal roadmap for the OpenCode Agent Ecosystem.
disable: true
hidden: true
---

# Opencode Setup & Agent Roster

My personal setup for OpenCode, detailing the agent hierarchy, specialized skills, and future roadmap for AI/ML and productivity tools.

---

## 🏗️ Global Agent Roster
The environment follows a modular, hierarchical structure where **Primary Agents** coordinate a specialized roster of **Sub-agents**.

### 1. Primary Agents (The Core Team)
*   **`orchestrator`**: The Project Manager. Translates blueprints into tasks, delegates to sub-agents, and maintains the `PROJECT_STATUS.md`.
*   **`architect`**: The Lead Designer. Focuses on Clean Architecture and Uncle Bob's principles. Produces sequential implementation plans.
*   **`codebase-analyst`**: The Onboarding Lead. Specialized in mapping existing codebases and coordinating documentation (`CODEBASE.md`).
*   **`doc-oracle`**: The Research & Mirroring Specialist. Deep-dives into OpenCode and Claude Code docs to mirror "Gold Standard" best practices.

### 2. Specialized Sub-agents (Execution Layers)

| Layer | Agent | Key Responsibilities |
| :--- | :--- | :--- |
| **App** | `backend-dev`, `frontend-dev`, `tester`, `ops-expert`, `technical-writer` | Full-stack application development, testing, and documentation. |
| **ML** | `data-engineer`, `model-scientist` | Data pipelines, ETL, model training, and evaluation. |
| **Util** | `clean-coder`, `research-analyst`, `security-reviewer`, `skill-creator`, `skill-tester`, `structure-expert`, `theory-deep-dive` | Specialized utilities for code quality, SOTA research, and skill building. |

---

## 🛠️ Global Skills
A collection of native OpenCode skills providing advanced capabilities across data, design, and automation.

| Category | Skill | Key Capabilities |
| :--- | :--- | :--- |
| **Data & ML** | `ml-data-import` | Support for CSV, Parquet, JSON, and large-file strategies. |
| | `xlsx` | Excel manipulation using pandas/openpyxl with formula recalculation. |
| | `pdf` | PDF generation, form handling, and document analysis. |
| **Development** | `mcp-builder` | Building Model Context Protocol servers in Node.js and Python. |
| | `webapp-testing` | Automated QA workflows for web applications. |
| **Design & UI** | `frontend-design` | Best practices for modern frontend architectures. |
| | `canvas-design` | UI/UX patterns and design systems. |
| | `theme-factory` | Curated UI themes (Midnight Galaxy, Arctic Frost, etc.). |
| **Productivity** | `internal-comms` | Standardized company updates, newsletters, and FAQs. |
| | `slack-gif-creator`| Specialized tool for interactive Slack content. |
| | `docx` | Word document creation and editing. |


---

## 🚀 Personal Setup & Roadmap
*Derived from the maintenance repository for this setup.*

### Current Features:
- **Anthropic-Inspired Skills**: Custom skills ported from Claude's ecosystem.
- **AI/ML Team**: Specialized agent team for end-to-end research and development.
- **Opencode Oracle**: Specialized agent for ecosystem customization and guidance.
- **Auto-Documentation**: Automated generation of project maps and theoretical audits.

### Upcoming features:
- Skills to:
  - Read different types of data inputs for ML (csv, parquet, zip, tar.gz, txt, json, more to be added)
  - FFMPEG executor - For video tasks at times. 
  - (Maybe) Handle text-based RPGs
  - Google doc skill
  - Calendar skill
  - Email checking skill
  - Canvas scraper (needs planning) - Academics retrieval.
  - ipynb skill (HIGH PRIORITY) - Read and write ipynbs effectively. No need to execute.
  - Sqlite/Postgres skill - CRUD operations, creation if not existing.
  - Project scan skill - Used by Updater sub-agent, for each project it'll scan the project and then gather information. Specifics TBD.
- Agents to:
  - Have **general utilities** for a system assistant (needs sub-agents)
    - _Planner sub-agent_ - Works with calendar, google doc, emails
  - (Maybe) RPG Orchestrator
  - **Homework Agent**
    - _Canvas sub-agent_ - Scrapes canvas using tools and skills to obtain assignments locally
    - _Builder sub-agent_ (existing?) - Builds project based on canvas assignment details
    - _Validator sub-agent_ (existing?) - Validates output of builder agent against the question inputs found by the Canvas sub-agent
  - **Resume Agent**
    - _Updater Sub-agent_ - Scans full project directory (avoids node-modules, .git folders), asks questions about experience, clarifying questions about projects, puts together updated master-skillset in a sqlite or postgres local db.
    - _Job Description sub-agent_ - Takes jd and company info, prioritizes important keywords, skills, experiences, projects necessary for role.
    - _Writer sub-agent_ - Converts updated master-skillset and experience, plus JD Sub-agent output into resume bullet points for resume content
    - _Publisher sub-agent_ - Uses pdf skill to push the writer's points into the finished resume.


---

## 📂 File System Standards
*   **Agent Definitions**: Stored as `.md` files with YAML frontmatter.
*   **Task Logging**: Every agent maintains logs in `.agent-tasks/<agent-name>/` (`PLAN.md`, `TASKS.md`, `STATUS.md`).
*   **User Alignment**: Agents read `~/.config/opencode/USER_DECISION_PROFILE.md` to adapt to user heuristics.
