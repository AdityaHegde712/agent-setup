---
description: Master Reference Guide for OpenCode Agents and Teams.
disable: true
hidden: true
---
# OpenCode Agents & Teams Master Reference Guide

This guide provides a comprehensive reference for configuring and orchestrating agents and agent teams in OpenCode, drawing from OpenCode's agent documentation and Claude Code's agent team orchestration patterns.

## 1. Agent Types

### Primary Agents
- **Definition**: The main assistants you interact with directly in a session.
- **Switching**: Cycle through them using `Tab` or the configured `switch_agent` keybind.
- **Built-in Primary Agents**:
    - **Build**: Default agent with all tools enabled. Used for full development work (file operations, system commands).
    - **Plan**: Restricted agent for analysis and review. Permissions for file edits and bash are set to `ask` by default.
    - **Compaction/Title/Summary**: Hidden system agents for context management.

### Subagents
- **Definition**: Specialized assistants invoked by primary agents or manually by the user.
- **Invocation**: Use `@agent_name` in your message (e.g., `@general find the bug`).
- **Built-in Subagents**:
    - **General**: Multi-step research and task execution. Full tool access except `todo`.
    - **Explore**: Read-only agent for exploring codebases. Cannot modify files.

---

## 2. Configuration Methods

### JSON Configuration (`opencode.json`)
Define agents within the `agent` object of your configuration file.

```json
{
  "agent": {
    "agent-name": {
      "description": "Short description of the agent's purpose",
      "mode": "primary | subagent",
      "model": "provider/model-id",
      "prompt": "System prompt text or {file:./path/to/prompt.txt}",
      "temperature": 0.1,
      "steps": 10,
      "permission": {
        "edit": "allow | ask | deny",
        "bash": "allow | ask | deny"
      }
    }
  }
}
```

### Markdown Configuration (Recommended)
Place `.md` files in:
- **Global**: `~/.config/opencode/agents/`
- **Project**: `.opencode/agents/`

The filename (e.g., `reviewer.md`) becomes the agent name.

**Structure**:
```markdown
---
description: Brief description of the agent
mode: subagent
model: anthropic/claude-3-5-sonnet
temperature: 0.1
permission:
  edit: deny
  bash: deny
steps: 5
---
System prompt content goes here. Define the agent's persona and specific focus.
```

---

## 3. Configuration Options

| Option | Description |
| :--- | :--- |
| **description** | (Required) Brief explanation of what the agent does. |
| **mode** | `primary` or `subagent`. |
| **model** | Override the default model (e.g., `anthropic/claude-3-5-sonnet`). |
| **prompt** | The system instructions. Can reference external files using `{file:path}`. |
| **temperature** | Controls randomness (0.0 - 1.0). Default is typically 0. |
| **steps** | Max agentic iterations before forcing a text-only response. |
| **permission** | Fine-grained tool control (e.g., `edit`, `bash`). |
| **disable** | Set to `true` to deactivate the agent. |
| **hidden** | If `true`, the agent won't appear in the UI/selection. |

---

## 4. Agent Teams Orchestration

Agent teams allow coordinating multiple sessions to work on shared tasks in parallel.

### Core Concepts
- **Lead Agent**: The main session that creates and manages the team.
- **Teammates**: Individual agent sessions spawned to handle specific tasks.
- **Shared Task List**: A centralized list of tasks that teammates can claim or be assigned.
- **Messaging**: Inter-agent communication allows teammates to share findings and coordinate.

### Team Commands & Patterns
- **Spawning a Team**: "Create an agent team to [task]. Spawn [N] teammates: [roles]."
- **Direct Interaction**: Switch to a teammate's session to provide specific feedback.
- **Shared Context**: Ensure teammates are given enough initial context (files, goals, constraints).
- **Quality Gates**: Use hooks like `TeammateIdle` or `TaskCompleted` to enforce reviews or tests.

### Best Practices for Teams
- **Task Sizing**: Ensure tasks are large enough to benefit from parallel work but small enough for clear deliverables.
- **Parallelism**: Use teams for research, competing hypotheses, or cross-layer features (frontend + backend + tests).
- **Coordination**: Start with research/review before implementation to align the team.
- **File Conflicts**: Assign distinct file areas to different teammates to avoid merge conflicts.
