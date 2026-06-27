---
description: Run the plan continuously and autonomously until complete
agent: orchestrator
---
You are executing in autonomous `/goal` mode.
Your objective is to fully complete the plan or goal described below:
$ARGUMENTS

Guidelines for Autonomous Execution:
1. Run continuously and autonomously without stopping until the plan is fully completed.
2. You have full authority to execute any shell commands to achieve this goal, EXCEPT for direct file deletion.
3. **CRITICAL (Deletion Rule)**: Do NOT use tools or commands to delete any files. If you need to delete a file (e.g., `file.py`), you MUST rename/prefix it (e.g., rename to `delete-file.py`) and then proceed as if it was deleted.
4. Execute the necessary steps, verify correctness at each stage, and report progress.
