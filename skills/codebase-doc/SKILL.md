---
name: codebase-doc
description: >
  Generate a comprehensive, professional CODEBASE.md file for any repository.
  Use this skill whenever a user asks to document, map, or explain a codebase, create
  a CODEBASE.md or codebase overview file, onboard a new developer or agent, produce
  architecture documentation, or generate a "brain dump" of how a project works.
  Trigger also when the user says things like "document this repo", "explain the
  codebase structure", "write a CODEBASE.md", "help agents understand this project",
  or "create codebase context for AI". The output is a single CODEBASE.md file at
  the repo root, structured for both human readers and AI coding agents.
license: MIT
compatibility: opencode
---

# Codebase Documentation Skill

Produces a professional `CODEBASE.md` at the repository root. The file serves two
audiences simultaneously: human developers onboarding to the project, and AI coding
agents that need persistent, structured context between sessions.

Read `references/sections.md` for the full section-by-section writing guide before
generating output. Read `references/quality.md` before finalizing.

---

## Workflow

### Step 1 — Gather facts before writing anything

Run these shell commands from the repository root. Do not write a single section
until you have their output in context.

```bash
# Directory tree (2 levels, skip noise)
find . -maxdepth 2 \
  -not -path './.git/*' \
  -not -path './node_modules/*' \
  -not -path './__pycache__/*' \
  -not -path './dist/*' \
  -not -path './build/*' \
  -not -path './.venv/*' \
  | sort

# Language / framework fingerprints
ls package.json pyproject.toml Cargo.toml go.mod pom.xml build.gradle \
   requirements.txt setup.py Makefile Dockerfile docker-compose.yml 2>/dev/null

# Entry points
grep -rl 'if __name__' . --include='*.py' | head -10
grep -rl '"main"' . --include='*.go' | head -5
grep -r '"scripts"' package.json 2>/dev/null | head -5

# Dependency count / key deps
cat package.json 2>/dev/null | python3 -c \
  "import json,sys; d=json.load(sys.stdin); \
   [print(k,v) for k,v in {**d.get('dependencies',{}), **d.get('devDependencies',{})}.items()]" \
  2>/dev/null | head -20
cat pyproject.toml 2>/dev/null | grep -A 30 '\[tool.poetry.dependencies\]'
cat requirements.txt 2>/dev/null | head -20

# Test locations
find . -name 'test_*.py' -o -name '*_test.py' -o -name '*.test.ts' \
       -o -name '*.spec.ts' -o -name '*.test.js' 2>/dev/null | head -10

# CI/CD
ls .github/workflows/ .gitlab-ci.yml Jenkinsfile 2>/dev/null

# Existing docs
ls README.md CONTRIBUTING.md CHANGELOG.md ARCHITECTURE.md docs/ 2>/dev/null
```

Also read these files directly if they exist:
- `README.md` — project description and intent
- `AGENTS.md` / `CLAUDE.md` — existing agent instructions (do not duplicate)
- Any `docker-compose.yml` — understand services and their relationships
- The 5–10 most-imported internal modules (grep for `from . import` / `require(`)

### Step 2 — Classify the codebase

Before writing, determine:

| Question | Answer drives |
|---|---|
| Architecture style? (monolith / microservices / library / CLI / serverless) | Overall framing |
| Primary language + runtime? | Tech stack section |
| Has tests? Has CI? | Development workflow section |
| Has a DB / cache / queue? | Data layer section |
| Who is the primary reader? (solo dev / team / open source contributors) | Depth and tone |

If the architecture is a **monorepo**, read `references/sections.md §Monorepo addendum`.

### Step 3 — Write CODEBASE.md

Follow the section order and rules in `references/sections.md`.

**Signal-to-noise principle:** Every sentence must convey something an agent or
developer could not infer by reading the code alone. Cut structural summaries that
mirror the directory tree. Prioritize counterintuitive patterns, architectural
constraints, and decisions-with-reasons.

**Length target:** 200–500 lines for a typical project. Larger codebases may go
longer but must use the progressive-disclosure technique (top-level summary +
linked sub-docs in `docs/architecture/`).

### Step 4 — Quality check

Run the checklist in `references/quality.md` before saving the file.

### Step 5 — Save and report

Write the file to the repo root as `CODEBASE.md`. Report to the user:
- File written at: `<path>/CODEBASE.md`
- Sections included (list)
- Any sections skipped and why (e.g. "No CI detected — skipped CI/CD section")
- Staleness risk items (file paths documented that may drift)

---

## Anti-patterns to avoid

- **Directory tree as content.** Never reproduce `tree` output verbatim as a section.
  File paths only appear when they illustrate a non-obvious pattern.
- **Auto-generated filler.** Sentences like "This project uses modern best practices"
  add zero information. Delete them.
- **Stale path references.** Every file path mentioned is a staleness liability.
  Prefer capability descriptions ("the auth module") over paths ("src/auth/index.ts")
  unless the path is stable and non-obvious.
- **Duplicating README.** CODEBASE.md is a complement to README.md, not a rewrite.
  Skip what the README already covers clearly. Link to it instead.
- **Bloat.** More rules do not produce better agent behavior. Keep the file focused.
  Rules accumulate and contradict — cut aggressively.
