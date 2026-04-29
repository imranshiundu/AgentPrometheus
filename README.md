# Agent Prometheus

**Agent Prometheus is an open-source AI workspace runtime built around one rule:**

```text
The system executes. The AI consults.
```

Prometheus is designed for developers who want AI assistance without giving a model blind control over a project. The runtime handles evidence collection, file filtering, diagnostics, task state, logs, approvals, and patch safety. The model receives a compact evidence packet and returns structured advice or small proposed changes.

This architecture makes the system usable with fast, cheaper, or less intelligent models because the hardest operational work is done by code before the model is asked to reason.

## What Agent Prometheus Is Building Toward

Agent Prometheus is intended to combine the best proven ideas from major open-source agent systems while keeping a safer Prometheus core:

- AutoGPT-style continuous workflows and reusable automation blocks
- OpenHands-style developer workspace control, file operations, terminal supervision, and sandbox discipline
- CrewAI-style roles, tasks, crews, flows, and structured orchestration
- GPT Engineer-style spec-to-code planning, project scaffolding, clarification loops, and verification cycles
- Prometheus-style evidence packets, weak-model reliability, Redis state, safety gates, patch review, and open-source inspectability

Prometheus should not become a blind autonomous fantasy system. It should become a serious runtime that can research, plan, propose, patch, test, document, and report through controlled execution.

## What This System Has Proven in the Current Codebase

The current `main` branch contains working source-level implementation for:

- Redis-backed task polling through `prometheus_tasks`
- workspace scanning with ignore rules
- evidence packet generation for selected project files
- support for Python, JavaScript, TypeScript, JSON, Markdown, YAML, TOML, INI, CSS, HTML, shell scripts, `Dockerfile`, and `*.Dockerfile` files
- safe Python syntax diagnostics using `compile()` without writing `.pyc` files or mutating the workspace
- filtering for noisy or sensitive paths including `.git`, `node_modules`, `venv`, `__pycache__`, `hive_mind_db`, images, archives, databases, and `.env`
- OpenAI-compatible model calls through LiteLLM or any compatible endpoint
- strict JSON-oriented consultant responses
- optional patch proposals using narrow operations
- path protection against edits outside the workspace
- protection against editing `.git`, `node_modules`, `venv`, `__pycache__`, and `hive_mind_db`
- Redis-backed logs and notifications
- kill-switch handling through `prometheus_kill_switch`
- Docker manager image installation from pinned `requirements.txt`
- upstream watcher for AutoGPT, OpenHands, CrewAI, and GPT Engineer design changes
- scheduled GitHub Action that can open a report PR when watched upstream repositories change

This means the core consultant-runtime pattern is present in code, not just described in the README.

## Verification Status

The repository currently proves the architecture at source level. Users should still run the local verification checklist before trusting it on a real project or server.

Recommended checks:

```bash
python -m compileall .
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs --tail=100
```

If Redis is running locally, you can push a test task:

```bash
redis-cli LPUSH prometheus_tasks '{"task":"Review the README and report missing setup steps."}'
```

Prometheus should poll the queue, scan the workspace, call the configured consultant model, and write logs/notifications through Redis.

## Why Agent Prometheus Exists

Most AI-agent systems become unreliable when the model is asked to do everything:

- discover project structure
- decide which files matter
- infer missing context
- run checks
- plan changes
- edit files
- explain what happened

Agent Prometheus separates those jobs. Code performs deterministic work. AI performs consulting work.

This is the core design advantage.

## Architecture

```text
User / Telegram / Dashboard
        |
        v
Redis task queue
        |
        v
Prometheus runtime
        |
        +--> scans workspace
        +--> filters unsafe/noisy paths
        +--> builds a repo map
        +--> selects relevant evidence
        +--> runs deterministic diagnostics
        +--> sends compact evidence to model through LiteLLM/OpenAI-compatible API
        +--> receives strict JSON plan / findings / patches
        +--> requests approval or applies patches only when explicitly enabled
        |
        v
Redis logs, notifications, reports, patch results
```

## Main Components

### `prometheus_consultant.py`

The evidence-driven consultant runtime.

Responsibilities:

- poll Redis for tasks
- build evidence packets from the workspace
- filter ignored, generated, sensitive, and binary-like files
- include runtime files such as Dockerfiles
- run safe Python syntax diagnostics
- call the configured model through an OpenAI-compatible API
- parse consultant JSON
- report findings, risks, tests to run, and proposed patches
- apply patches only when `PROMETHEUS_AUTO_APPLY=true`
- block dangerous paths
- emit logs and notifications

### `prometheus_manager.py`

Manager entrypoint for starting the Prometheus runtime. In this architecture, the manager should route work to the consultant runtime rather than treating the model as a fully trusted executor.

### `tools/upstream_watch.py`

Safe upstream repository watcher.

It checks selected public repositories and writes local Markdown reports when their default branch changes. It does not copy source code from upstream projects.

Watched projects:

- `Significant-Gravitas/AutoGPT`
- `All-Hands-AI/OpenHands`
- `crewAIInc/crewAI`
- `gpt-engineer-org/gpt-engineer`

### `.github/workflows/upstream-watch.yml`

Scheduled GitHub Action that runs the upstream watcher and opens a PR if new upstream reports are generated.

### `docs/UPSTREAM_FEATURE_MAP.md`

Design map explaining how Prometheus should learn from AutoGPT, OpenHands, CrewAI, and GPT Engineer without becoming a copy of any of them.

### `config/litellm_config.yaml`

Model routing layer. Prometheus is provider-neutral when routed through LiteLLM.

Recommended aliases:

```text
consultant-model   -> main reasoning / planning model
utility-model      -> cheaper triage / summarization model
review-model       -> optional stronger final review model
```

These aliases can point to Groq, OpenAI, Anthropic, Gemini, local OpenAI-compatible servers, or any provider supported by your LiteLLM setup.

### `docker/Manager.Dockerfile`

Manager container definition. It installs pinned Python dependencies from `requirements.txt` for reproducible builds.

### `.prometheusignore`

Optional project-level ignore file for excluding private, generated, or irrelevant files.

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

## Consultant Runtime Flow

```text
1. Receive task from Redis
2. Scan workspace
3. Apply ignore rules
4. Select likely relevant files
5. Read bounded file samples
6. Run deterministic diagnostics
7. Build evidence packet
8. Ask model for strict JSON
9. Report findings and patches
10. Apply patches only if auto-apply is enabled
11. Emit logs and notifications
```

## Model Strategy

Agent Prometheus is designed to work with weak or cheap models by reducing the job given to the model.

The model is not asked to explore the full project blindly. It receives a controlled packet containing selected files, diagnostics, rules, and the user task.

### Groq-first setup

Typical environment variables:

```bash
OPENAI_API_BASE=http://litellm:4000/v1
OPENAI_API_KEY=sk-local-litellm-key
PROMETHEUS_CONSULTANT_MODEL=consultant-model
PROMETHEUS_CHEAP_MODEL=utility-model
PROMETHEUS_AUTO_APPLY=false
```

Your Groq key belongs in `.env` or your server secret manager. Never commit provider keys to GitHub.

### Recommended model roles

```text
utility-model      -> cheap classification, summaries, simple routing
consultant-model   -> main code review, planning, and evidence interpretation
review-model       -> optional second pass for risky patches
```

## Upstream Update Strategy

Prometheus can watch upstream repositories, but it must not automatically copy code.

Safe update loop:

```text
1. Watch upstream repo metadata
2. Detect latest commit changes
3. Write a local update report
4. Open a PR for maintainers
5. Human reviews what changed
6. Prometheus implements only selected ideas in original code
7. Tests and docs are updated before merge
```

Run manually:

```bash
python tools/upstream_watch.py
```

The scheduled GitHub Action can run weekly and open a pull request with new reports.

## Safety Model

Prometheus is built to be safe by default.

Default behavior:

- read bounded samples instead of dumping entire projects into the model
- ignore secrets, generated folders, binary-heavy files, images, archives, databases, and `.env`
- avoid workspace mutation during diagnostics
- block path traversal
- block protected-directory edits
- require exact patch operations
- keep automatic patching disabled unless explicitly enabled
- log what the runtime is doing
- report missing evidence instead of pretending
- watch upstream projects without copying their code

Auto-apply is disabled by default:

```bash
PROMETHEUS_AUTO_APPLY=false
```

Enable it only in a trusted local environment with backups:

```bash
PROMETHEUS_AUTO_APPLY=true
```

## Patch Format

The model can propose narrow patch operations.

Replace operation:

```json
{
  "op": "replace",
  "path": "relative/path.py",
  "find": "exact old text",
  "replace": "exact new text"
}
```

Write-file operation:

```json
{
  "op": "write_file",
  "path": "docs/example.md",
  "content": "full file content"
}
```

The runtime validates paths before writing.

## Hardware Requirements

### Minimum local test

- 2 CPU cores
- 4 GB RAM
- 10 GB free disk
- Python 3.11
- Node.js 18+
- Docker Engine
- Docker Compose v2

### Recommended developer machine

- 4+ CPU cores
- 8 GB RAM minimum
- 16 GB RAM preferred
- 30 GB free disk
- Ubuntu 24.04 LTS, Debian, macOS, or WSL2
- Python 3.11
- Node.js 18 or 20
- Docker Engine + Compose v2

### VPS sizing

Basic always-on setup:

- 2 vCPU
- 4 GB RAM
- 25 GB disk

Stable setup:

- 4 vCPU
- 8 GB RAM
- 40 GB disk

Heavy automation or browser/sandbox workflows:

- 8 vCPU
- 16 GB RAM or more
- 80 GB disk or more

## Installation

Clone the repository:

```bash
git clone https://github.com/imranshiundu/AgentPrometheus.git
cd AgentPrometheus
```

Create an environment file:

```bash
cp .env.example .env 2>/dev/null || touch .env
```

Add runtime settings:

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

Install dependencies or use Docker:

```bash
pip install -r requirements.txt
```

Start services:

```bash
docker compose up -d --build
```

Run the consultant runtime directly:

```bash
python prometheus_consultant.py
```

## Redis Task Payload

Prometheus polls Redis list `prometheus_tasks`.

Example task:

```json
{
  "task": "Review the authentication module and propose safe fixes.",
  "chat_id": 123456789
}
```

Push a task manually:

```bash
redis-cli LPUSH prometheus_tasks '{"task":"Review README and find missing setup steps."}'
```

## Expected Consultant Response

The model is instructed to return JSON shaped like this:

```json
{
  "summary": "Evidence-based summary.",
  "findings": [],
  "plan": [],
  "patches": [],
  "tests_to_run": [],
  "risks": [],
  "missing_evidence": [],
  "confidence": "medium"
}
```

## Open-Source Contributor Rules

Contributors should keep the project honest and inspectable.

When adding a feature, document:

- what it reads
- what it writes
- what it executes
- what data leaves the machine
- which environment variables it needs
- how to disable it
- how to test it

Never commit:

- `.env`
- API keys
- Telegram bot tokens
- private SSH keys
- database dumps
- local logs with secrets
- user data
- model provider credentials

## Release Checklist

Before tagging a release:

1. run Python compile checks
2. validate Docker Compose
3. build containers
4. confirm Redis task flow works
5. confirm no secrets are committed
6. confirm README matches actual code
7. test with `PROMETHEUS_AUTO_APPLY=false`
8. test one approved patch flow locally
9. document known issues
10. tag the release

## Roadmap

Near-term:

- CI workflow for compile and Docker Compose validation
- clearer `.env.example`
- task dashboard for consultant reports
- approval queue for proposed patches
- rollback snapshots before file edits
- LiteLLM fallback chain
- release tags with tested setup notes
- workflow block schema
- flow runner
- upstream update reports

Later:

- policy engine for command execution
- per-repository memory
- sandboxed execution
- structured test runner
- web UI for task creation and review
- plugin system for integrations
- Agent Protocol adapter
- benchmark suite
- multi-role Prometheus crews

## Project Positioning

Agent Prometheus is an AI-native workspace runtime for controlled automation.

It is built to inspect projects, collect evidence, consult AI models, propose safe changes, and support developer-controlled execution. The current codebase proves the core consultant-runtime pattern and is ready for open-source users to inspect, run, test, improve, and build from.
