---
disable: true
---

# Orchestrator Protocols & Operational Handbooks

## Dynamic Sub-agents Note
- Dynamic sub-agents are project-native, created by `@sub-agent-creator` during planning.
- Stored in `.opencode/agents/` with the `dynamic-` prefix.
- Listed in `.agent-tasks/architect/AGENT_TEAM.md` by the Architect.
- Available via `@dynamic-name` (or `@local-dynamic-name`) once created.

---

## Gap Fallback Protocol
Ideally, there should never be unforeseen tasks or unmapped task gaps during execution. However, if the Orchestrator encounters an unforeseen task gap at runtime (e.g. an unexpected step that cannot be delegated to any of the existing static or dynamic agents):

1. Create a **stub** for that gap task (such as a placeholder file or script).
2. Complete the remaining tasks as per the plan.
3. At the end of execution, in the final SUMMARY of the completed work, report the task gap clearly to the Owner. This avoids disrupting long-running or overnight tasks.

---

## Step Exhaustion Recovery Protocol
When executing tasks, sub-agents may run out of steps before completing their assigned work. When a sub-agent hits its steps limit, it will exit and return a text-only summary of the tasks completed so far and tasks remaining.

To recover and ensure task completion:
1. **Detect Step Exhaustion**: Check the sub-agent's return output for incomplete tasks or messages indicating step exhaustion.
2. **Re-invocation Loop**: If tasks are left incomplete, parse the sub-agent's progress summary and re-invoke the same sub-agent to continue the remaining work, passing the previous progress context.
3. **Loop Capping**: Track the number of re-invocations for the same task cluster. To prevent infinite loops, cap the maximum number of consecutive re-invocations to **5** per task cluster. If it fails to complete after 5 re-invocations, halt and report the state to the Owner.

---

## Communication Protocols
- Act as the primary point of contact for the Owner during the build phase.
- **Manual Intervention**: Handle requests from sub-agents for manual Owner tasks (e.g., dataset downloads or auth blocks). Pause the sub-agent's task, ask the Owner to clear the bottleneck, and resume the sub-agent once resolved.
- If a sub-agent raises a "Snag," translate it for the Owner and facilitate a resolution.
- When dynamic agents are used, briefly inform the Owner: *"I am using `@dynamic-name` for [tasks] as specified in the plan."*
