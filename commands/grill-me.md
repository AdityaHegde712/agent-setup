---
description: Interview the user to align on a plan and resolve design decisions one-by-one
agent: architect
---
The user wants to align on a plan using the `/grill-me` process, starting with the prompt:
$ARGUMENTS


You MUST interview the user about every aspect of their task until you've reached a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one.

Guidelines:
- Ask the questions one at a time.
- For each question, provide your recommended answer.
- Do not dump all questions at once.
- **CRITICAL**: Use the native `question` tool to present options to the user. Do not print questions as standard text chat unless the tool fails or is unavailable. This saves tokens and keeps the conversation history clean.
- Once all questions are resolved, summarize the decisions and outline the final design/plan.
