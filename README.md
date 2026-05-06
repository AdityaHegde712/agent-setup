# Opencode Setup

My personal setup for opencode, describing agents, skills, and other tools.

## Added features:
- Skills ripped off from Anthropic
- Agent team for AI/ML projects
- Opencode Oracle Agent to customize Opencode
- Documentation agent

## Upcoming features:
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
