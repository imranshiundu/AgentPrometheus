# Agent Prometheus

Agent Prometheus is an open-source, local-first automation runtime for research, code review, project inspection, and controlled task execution.

The safest architecture is simple:

```text
The system executes. The AI consults.
```

That means Prometheus should not treat the language model as an all-knowing commander. The runtime scans the project, collects evidence, runs deterministic checks, stores state, keeps logs, applies safety rules, and only then asks an AI model for structured advice. This makes the system cheaper, safer, and more useful with weaker or faster models, including Groq-hosted models.

## Current Main Branch Status

The main branch has been moved toward consultant-mode operation.

Included in main:

- evidence-driven consultant runtime in `prometheus_consultant.py`
- safe Python syntax diagnostics that do not create `.pyc` files
- Dockerfile and `*.Dockerfile` evidence detection
- stronger ignore rules for `.git`, `node_modules`, `venv`, `__pycache__`, `hive_mind_db`, binaries, images, archives, databases, and `.env`
- provider-neutral LiteLLM/OpenAI-compatible model access
- default approval-first behavior for edits
- Redis task queue, logs, notifications, and kill-switch hooks
- documentation explaining the project from first principles

Open branches may still exist on GitHub for audit/history, but the important consultant runtime fixes have been applied to main.

## What Problem This Solves

Most agent systems fail because they ask an LLM to do too much:

- read too many files at once
- guess missing context
- run actions without evidence
- burn tokens on irrelevant content
- hallucinate successful tests
- mutate workspaces while only "checking" them
- behave dangerously when paired with a small or weak model

Agent Prometheus is being hardened to avoid that failure mode. It narrows the AI role to consulting over verified evidence.

## Core Architecture

```text
User / Telegram / Dashboard
        |
        v
Redis task queue
        |
        v
Prometheus runtime
        |
        +--> scans workspace files
        +--> filters ignored / unsafe paths
        +--> collects small evidence packets
        +--> runs deterministic diagnostics
        +--> sends compact context to model through LiteLLM
        +--> receives strict JSON advice
        +--> requests approval or applies patches if explicitly allowed
        |
        v
Logs, notifications, reports, patch results
```

## Main Components

### `prometheus_consultant.py`

The consultant runtime. It:

- polls Redis for tasks
- builds an evidence packet from the workspace
- ignores noisy or dangerous paths
- includes source files, config, Markdown, shell scripts, Dockerfiles, and `*.Dockerfile` files
- runs Python syntax diagnostics using `compile()` instead of `py_compile.compile()` so scans do not create `__pycache__`
- calls the configured model through an OpenAI-compatible endpoint
- forces the model to return structured JSON
- supports safe patch operations
- blocks path traversal and protected-directory edits
- sends logs and notifications back through Redis

### `prometheus_manager.py`

The manager entrypoint. In the hardened direction, this should route to the consultant runtime instead of pretending the AI is a fully autonomous commander.

### `config/litellm_config.yaml`

LiteLLM model routing. The project should use aliases such as:

- `consultant-model`
- `utility-model`
- `review-model`

Those aliases can point to Groq, OpenAI, Anthropic, Gemini, local OpenAI-compatible servers, or any provider LiteLLM supports.

### `docker-compose.yml`

Container orchestration for the supporting stack. Depending on the branch and local setup, this may include Redis, LiteLLM, ChromaDB, backend/dashboard services, manager/runtime services, and Telegram-facing services.

### `.prometheusignore`

Optional project-level ignore file. Use it to stop Prometheus from scanning secrets, generated files, logs, databases, or large folders.

Example:

```gitignore
logs/**
dist/**
build/**
coverage/**
*.pem
*.key
private/**
```

## Why Consultant Mode Works Better

Consultant mode is designed for weak-model reliability.

Instead of sending the whole repo to a model and saying "fix everything", the runtime does the boring work first:

1. map the workspace
2. remove irrelevant files
3. select only likely-relevant evidence
4. run deterministic checks
5. ask the model for JSON only
6. require exact patch operations
7. avoid automatic edits unless enabled
8. report uncertainty instead of pretending

This is how you make Groq-speed models useful. They get cleaner context and a smaller job.

## Model Strategy

### Recommended default

Use a fast, cheaper model for routine consulting and a stronger model only when the task is difficult.

Example model roles:

```text
utility-model      -> cheap classification, summaries, simple triage
consultant-model   -> main planning and code review
review-model       -> final review before applying risky changes
```

### Groq-first setup

Groq can work well when:

- evidence packets are small
- prompts demand JSON
- temperature is low
- the runtime verifies results
- the model is not allowed to directly run broad actions

Typical environment variables:

```bash
OPENAI_API_BASE=http://litellm:4000/v1
OPENAI_API_KEY=sk-any-local-litellm-key
PROMETHEUS_CONSULTANT_MODEL=consultant-model
PROMETHEUS_CHEAP_MODEL=utility-model
PROMETHEUS_AUTO_APPLY=false
```

Your real Groq key should be placed in `.env` or your server secret manager, never committed to GitHub.

## Safety Model

Prometheus should be safe by default.

Default behavior:

- scan only allowed text/code files
- ignore secrets and generated folders
- do not write `.pyc` files during diagnostics
- do not edit `.git`, `node_modules`, `venv`, `__pycache__`, or `hive_mind_db`
- do not edit outside the workspace
- do not auto-apply patches unless `PROMETHEUS_AUTO_APPLY=true`
- log decisions
- report missing evidence
- refuse unsupported patch operations

The AI is allowed to advise. The runtime decides what can be executed.

## Hardware Requirements

### Minimum local test

Use this only to inspect the stack and run light tasks.

- CPU: 2 cores
- RAM: 4 GB
- Disk: 10 GB free
- OS: Ubuntu 22.04/24.04, Debian, macOS, or WSL2
- Python: 3.11 recommended
- Node.js: 18+
- Docker Engine
- Docker Compose v2

### Recommended developer machine

Good for normal development, Docker services, Telegram testing, and Groq/LiteLLM use.

- CPU: 4 cores or more
- RAM: 8 GB minimum
- RAM: 16 GB preferred
- Disk: 30 GB free
- OS: Ubuntu 24.04 LTS recommended
- Python: 3.11
- Node.js: 18 or 20
- Docker Engine + Compose v2
- stable internet connection

### VPS sizing

Basic always-on setup:

- 2 vCPU
- 4 GB RAM
- 25 GB disk

Stable setup:

- 4 vCPU
- 8 GB RAM
- 40 GB disk

Heavy setup with browser automation, sandboxes, or OpenHands-like services:

- 8 vCPU
- 16 GB RAM or more
- 80 GB disk or more

Do not run heavy browser automation on a 1 GB RAM server.

## Installation

Clone the repository:

```bash
git clone https://github.com/imranshiundu/AgentPrometheus.git
cd AgentPrometheus
```

Create or update your environment file:

```bash
cp .env.example .env 2>/dev/null || touch .env
```

Add your keys and runtime settings:

```bash
REDIS_HOST=redis
REDIS_PORT=6379

OPENAI_API_BASE=http://litellm:4000/v1
OPENAI_API_KEY=sk-local-litellm-key

PROMETHEUS_CONSULTANT_MODEL=consultant-model
PROMETHEUS_CHEAP_MODEL=utility-model
PROMETHEUS_WORKSPACE=workspace
PROMETHEUS_AUTO_APPLY=false
PROMETHEUS_MAX_FILES=120
PROMETHEUS_MAX_FILE_CHARS=6000
PROMETHEUS_EVIDENCE_BUDGET=28000
```

Run setup if provided:

```bash
chmod +x setup.sh
./setup.sh
```

Start Docker services:

```bash
docker compose up -d --build
```

Check logs:

```bash
docker compose ps
docker compose logs -f --tail=100
```

## Running the Consultant Runtime Locally

Install Python dependencies according to the repository requirements, then run:

```bash
python prometheus_consultant.py
```

The runtime polls Redis list `prometheus_tasks`.

A task payload should look like:

```json
{
  "task": "Review the authentication module and propose safe fixes.",
  "chat_id": 123456789
}
```

Push it manually with Redis CLI:

```bash
redis-cli LPUSH prometheus_tasks '{"task":"Review README and find missing setup steps."}'
```

## Expected Consultant Response Shape

The model is instructed to return JSON like:

```json
{
  "summary": "Short evidence-based summary.",
  "findings": [],
  "plan": [],
  "patches": [],
  "tests_to_run": [],
  "risks": [],
  "missing_evidence": [],
  "confidence": "medium"
}
```

Patch operations are intentionally narrow:

```json
{
  "op": "replace",
  "path": "relative/path.py",
  "find": "exact old text",
  "replace": "exact new text"
}
```

or:

```json
{
  "op": "write_file",
  "path": "docs/example.md",
  "content": "full file content"
}
```

## Testing Checklist

Before trusting a change, run:

```bash
python -m compileall .
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs --tail=100
```

If a backend health endpoint exists:

```bash
curl http://localhost:8000/health
```

If Telegram is enabled:

```text
/start
/status
```

Then inspect Redis logs or dashboard logs.

## Merge and Release Checklist

Before merging a branch into main:

1. compare branch against main
2. inspect changed files
3. resolve conflicts manually
4. run Python compile checks
5. validate Docker Compose
6. build containers
7. confirm no secrets are committed
8. confirm README and docs match the code
9. merge only after the branch is safe
10. tag a release only after real local or VPS testing

## Security Rules for Contributors

Never commit:

- `.env`
- API keys
- Telegram bot tokens
- private SSH keys
- database dumps
- local logs with secrets
- user data
- model provider credentials

When adding an integration, document:

- what data it reads
- what data it writes
- whether it can execute commands
- where credentials are stored
- how to disable it

## Known Limitations

- This is still experimental software.
- Docker integration must be tested on a real local machine or VPS.
- Small models can still produce bad advice.
- Consultant mode reduces hallucination risk but does not eliminate it.
- Automatic patching should stay disabled until the project has strong tests and rollback gates.
- Some branches may remain visible for audit/history even after main receives the important fixes.

## Roadmap

Near-term:

- stronger health checks
- CI workflow for Python compile and Docker Compose validation
- clearer `.env.example`
- smaller service profiles for low-RAM VPS usage
- dashboard page for consultant reports
- approval queue for proposed patches
- rollback snapshots before file edits
- model fallback chain through LiteLLM

Later:

- policy engine for command execution
- per-repository memory
- safer sandbox execution
- structured test runner
- web UI for task creation and review
- contributor guide and release process

## Honest Positioning

Agent Prometheus is not magic. It is not fully autonomous. It is not guaranteed to build production systems alone.

The correct promise is:

```text
Agent Prometheus helps a developer inspect, plan, review, and safely automate project work by combining deterministic runtime checks with AI consultation.
```

That is strong enough, honest enough, and safer for open-source users.
