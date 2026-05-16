# Agent Prometheus

**Agent Prometheus is an open-source AI workspace runtime built around one rule:**

```text
The system executes. The AI consults.
```

Prometheus is one unified runtime for controlled developer automation: task intake, evidence collection, repository indexing, deterministic diagnostics, model consultation, guarded patch proposals, logs, notifications, artifacts, and human approval.

The public-facing system name is **Agent Prometheus**. References to outside projects such as AutoGPT, OpenHands, CrewAI, and GPT Engineer are treated as implementation inspiration or optional adapters, not as user-facing product identities.

## Current Unified Architecture

```text
Telegram / Dashboard
        |
        v
Redis task queue: prometheus_tasks
        |
        v
Prometheus consultant runtime
        |
        +--> scans workspace
        +--> filters unsafe/noisy paths
        +--> builds repository index
        +--> runs deterministic diagnostics
        +--> sends compact evidence to consultant-model through LiteLLM
        +--> receives strict JSON plan / findings / patch proposals
        +--> applies patches only when explicitly enabled
        |
        v
Redis logs, notifications, artifacts, reports
        |
        v
Dashboard / Telegram output
```

## Runtime Principle

Prometheus keeps deterministic work in code and advisory work in the model.

The model is not asked to blindly explore a project, mutate files, run unknown commands, or pretend tests passed. The runtime gathers evidence first, then asks the model for structured advice.

## What Prometheus Does

- accepts tasks from the dashboard or Telegram
- queues work through Redis
- scans the mounted workspace
- ignores noisy, generated, binary-heavy, and sensitive paths
- indexes repository structure, entrypoints, dependency files, API routes, Redis touchpoints, environment variables, imports, and Python symbols
- compiles Python files safely without mutating the workspace
- builds bounded evidence packets
- calls an OpenAI-compatible model through LiteLLM
- parses consultant responses as strict JSON
- reports findings, risks, missing evidence, tests to run, and patch proposals
- blocks path traversal and protected-directory edits
- keeps automatic patching disabled unless explicitly enabled
- publishes runtime logs and notifications through Redis
- exposes runtime state through a FastAPI backend
- displays live status and logs in the dashboard

## Service Map

| Service | Purpose | Default Port |
|---|---|---:|
| `litellm` | Model gateway and provider router | `4000` |
| `redis` | Queue, logs, notifications, control state | internal |
| `chromadb` | Persistent memory store | `8001` |
| `prometheus-orchestrator` | Unified consultant runtime | internal |
| `prometheus-frontdesk` | Telegram gateway | internal |
| `backend` | FastAPI dashboard/runtime API | `8000` |
| `dashboard` | Vite React dashboard | `5173` |
| `vision-bridge` | Optional paired observation bridge | `8765` |
| `openhands` | Optional external sandbox service | internal |

## Runtime API

The dashboard backend exposes:

```text
GET    /health
GET    /stats
GET    /logs
WS     /ws/logs
POST   /tasks
POST   /control/kill-switch
DELETE /control/kill-switch
GET    /artifacts
GET    /vision_node.py
```

The dashboard uses these routes directly. It does not treat static demo logs as runtime truth.

## Main Runtime Files

### `prometheus_consultant.py`

Primary runtime. It polls Redis, scans the workspace, builds evidence packets, calls the model, validates responses, reports results, and optionally applies guarded patches.

### `prometheus_indexer.py`

Repository indexing layer. It detects languages, entrypoints, dependency files, Docker/Compose files, API routes, Redis touchpoints, environment variables, imports, Python functions, and classes.

### `prometheus_json.py`

Strict JSON repair and normalization layer for consultant responses.

### `backend/src/main.py`

FastAPI backend for runtime status, logs, dashboard task creation, artifact listing, and control actions.

### `telegram_gateway.py`

Owner-authorized Telegram gateway for task intake, notifications, approvals, voice task transcription, and kill-switch signaling.

### `memory_ledger.py`

Persistent lesson store backed by ChromaDB. This is internal runtime memory, not a separate user-facing agent.

### `prometheus_manager.py`

Legacy orchestration experiment. It is retained for reference while the unified consultant runtime becomes the main path. Do not treat this file as the production entrypoint unless it is intentionally rewired to delegate to `prometheus_consultant.py`.

## Model Routing

Prometheus uses LiteLLM model aliases rather than hardcoding providers throughout the runtime.

Recommended aliases:

```text
consultant-model   -> main evidence-based planning/review model
utility-model      -> cheaper triage and summaries
coding-model       -> optional coding/sandbox model
research-model     -> optional long-context research model
```

`consultant-model` is the default route for the unified runtime.

## Running Locally

```bash
docker compose up -d --build
```

Then open:

```text
Dashboard: http://localhost:5173
Backend:   http://localhost:8000/health
LiteLLM:   http://localhost:4000
```

Push a task manually:

```bash
redis-cli LPUSH prometheus_tasks '{"task":"Review the workspace and report disconnected routes."}'
```

Or submit a task from the dashboard.

## Consultant Response Contract

The model is instructed to return JSON with this shape:

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

Patch proposal format:

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

## Safety Model

Prometheus is safe by default:

- auto-apply is disabled by default
- evidence packets are bounded
- `.env`, generated folders, dependency folders, archives, databases, and binary-heavy files are ignored
- Python syntax checks use `compile()` and do not write `.pyc` files
- protected paths such as `.git`, `node_modules`, `venv`, `__pycache__`, and `hive_mind_db` cannot be edited
- path traversal is blocked
- logs are published to Redis for inspection
- missing evidence is reported instead of guessed

Enable automatic patching only in a trusted local workspace with backups:

```bash
PROMETHEUS_AUTO_APPLY=true
```

## Naming Policy

Public-facing names should use Agent Prometheus language:

| Public Name | Internal Meaning |
|---|---|
| Command Center | Dashboard task and runtime view |
| Runtime Memory | Chroma-backed lesson store |
| Evidence Reports | Repository scans, diagnostics, and findings |
| Artifact Registry | Generated files and production outputs |
| Runtime Settings | Model/config/control surface |
| Consultant Runtime | Evidence-based model consultation loop |
| Observation Bridge | Optional paired visual context bridge |

Avoid exposing upstream project names in user-facing UI unless describing optional integrations or design inspiration.

## Upstream Inspiration Map

Prometheus borrows ideas, not identity:

- AutoGPT inspired reusable workflows and long-running automation loops.
- OpenHands inspired workspace control, sandbox discipline, and developer tooling.
- CrewAI inspired role/task/flow vocabulary, but Prometheus should not rely on blind multi-agent execution as the core safety model.
- GPT Engineer inspired spec-to-code planning and verification loops.

These ideas are consolidated into one runtime rather than presented as separate products.

## Verification

Recommended checks:

```bash
python -m py_compile prometheus_consultant.py prometheus_indexer.py prometheus_json.py backend/src/main.py telegram_gateway.py vps_receiver.py
python -m pytest -q tests/test_consultant_runtime.py
docker compose config
docker compose up -d --build
docker compose ps
curl http://localhost:8000/health
```

## Current Focus

Near-term priorities:

1. keep `prometheus_consultant.py` as the production runtime entrypoint
2. keep dashboard routes connected to backend routes
3. remove or archive stale public-facing documentation from old sub-agent folders
4. rename user-facing folder/docs language without breaking imports or compose mounts
5. expand CI to verify all maintained runtime files
6. add stronger approval flow for patch proposals
7. add artifact download and report history

## Project Positioning

Agent Prometheus is an AI-native workspace runtime for controlled automation.

It inspects projects, collects evidence, consults models, proposes safe changes, and supports developer-controlled execution through one unified system.
