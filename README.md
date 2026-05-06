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
  - FFMPEG executor
  - (Maybe) Handle text-based RPGs
  - Google doc skill
  - Calendar skill
  - Email checking skill
  - Canvas scraper (needs planning)
  - ipynb skill (HIGH PRIORITY) 
- Agents to:
  - Have general utilities for a system assistant (needs sub-agents)
    - Planner sub-agent - Works with calendar, google doc, emails
  - (Maybe) RPG Orchestrator
  - Homework
    - Canvas sub-agent - Scrapes canvas using tools and skills to obtain assignments locally
    - Builder sub-agent (existing?) - Builds project based on canvas assignment details
    - Validator sub-agent (existing?) - Validates output of builder agent against the question inputs found by the Canvas sub-agent
