---
name: task-paralysis-break
description: Overcome decision fatigue and task paralysis. Trigger when the user mentions 'task paralysis', 'Task paralysis: Task A, B, or C', or feels stuck between tasks. Use when the user asks 'Which task should I do?', 'Pick a task for me', or presents a list of choices and asks for a decision.
---

# Task Paralysis Break Skill

This skill is designed to help the user break through task paralysis and procrastination by quickly delivering a decisive choice, a clear rationale, and a sequenced plan of action if there are multiple tasks.

## Handling Task Paralysis

When the user is struggling with task paralysis (e.g., they say "Task paralysis: Task A, B, or C", or are stuck between choices), execute the following steps:

1. **Extract the Tasks**: Identify all tasks the user is deciding between.
2. **Analyze and Sequence**:
   - **Unequal Priorities**: Identify the task with the highest consequence if delayed. Recommend focusing on that task first. Provide a brief, decisive rationale contrasting it with low-impact or "quick win" distractions.
   - **Similar Priorities**: Pick one task at random to start with.
   - **Sequencing (3 or more tasks)**: If there are 3 or more tasks, arrange them in a sensible sequence starting with the quickest/easiest task first to build initial momentum.
3. **Deliver Response**:
   - Deliver the response with confidence, clarity, and directness. Avoid excessive empathy or open-ended follow-up questions.
   - Provide a clear, decisive rationale for the recommendation.
   - Present the first task in **bold**.

## Example Responses

### Example 1: Similar Priorities (Random Selection & Sequencing)
**Input**: "Task paralysis: respond to email, wash the dishes, or fold laundry."
**Response**: 
"Since it's the quickest, **respond to email** is your first task. Then you can take care of doing the dishes and then folding the laundry."

### Example 2: Unequal Priorities (Priority Determination)
**Input**: "Task paralysis: study for exam tomorrow morning, or organize my bookshelf."
**Response**:
"While it may feel like organizing your bookshelf gives you a quick win, it can wait, because the exam has a higher consequence. **Focus on your exam**, organize your bookshelf after it's over tomorrow."
