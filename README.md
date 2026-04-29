# Agent Prometheus

Agent Prometheus is an evidence-driven automation runtime that uses AI as a consultant, not as imaginary hands.

The system performs the work: scanning folders, selecting files, running deterministic checks, collecting logs, queueing tasks, applying approved patches, and producing reports. The AI model is consulted for judgement: diagnosis, planning, review, risk analysis, and patch suggestions.

This architecture is designed to work even with cheap or weak models because the runtime sends small evidence packets instead of asking the model to understand the whole project at once.

## Core idea

```text
The system executes. The AI consults.
```

Agent Prometheus avoids the fragile “multi-agent fantasy” pattern where models pretend they tested code or inspected files. A model must only reason from evidence the runtime gives it.

## What the runtime does

- scans the workspace
- builds a repo map
- reads relevant text files safely
- ignores secrets, binaries, dependency folders, and build artifacts
- runs Python compile checks
- creates compact evidence packets
- asks a provider-neutral model through LiteLLM
- accepts strict JSON consultant plans
- proposes or applies small patch operations
- reports results to Redis, backend, dashboard, and Telegram front desk

## What the AI does

- interprets evidence
- identifies likely causes
- proposes minimal patches
- lists tests to run
- warns about risk
- requests missing evidence instead of guessing

## Weak-model friendly design

Cheap models fail when they are given vague instructions and a giant codebase. Agent Prometheus reduces the task into structured evidence and strict JSON.

Default mode is safe:

```env
PROMETHEUS_AUTO_APPLY=false
```

That means the model can suggest changes, but Prometheus will not write files unless auto-apply is enabled or approval logic is added by the operator.

## Quick start

```bash
git clone https://github.com/imranshiundu/AgentPrometheus.git
cd AgentPrometheus
./setup.sh
docker compose up -d
curl http://localhost:8000/health
```

Then open:

```text
Dashboard: http://localhost:5173
Backend:   http://localhost:8000
LiteLLM:   http://localhost:4000
ChromaDB:  http://localhost:8001
```

## Model setup

Agent Prometheus is provider-neutral. Use any LiteLLM-supported provider.

Cheap Groq profile:

```env
PROMETHEUS_CONSULTANT_PROVIDER_MODEL=groq/llama-3.1-8b-instant
PROMETHEUS_REVIEW_PROVIDER_MODEL=groq/llama-3.1-8b-instant
PROMETHEUS_UTILITY_PROVIDER_MODEL=groq/llama-3.1-8b-instant
GROQ_API_KEY=your_key_here
PROMETHEUS_CONSULTANT_API_KEY=your_key_here
PROMETHEUS_REVIEW_API_KEY=your_key_here
PROMETHEUS_UTILITY_API_KEY=your_key_here
```

Balanced profile:

```env
PROMETHEUS_CONSULTANT_PROVIDER_MODEL=groq/llama-3.1-70b-versatile
PROMETHEUS_REVIEW_PROVIDER_MODEL=groq/llama-3.1-70b-versatile
PROMETHEUS_UTILITY_PROVIDER_MODEL=groq/llama-3.1-8b-instant
```

Premium profile:

```env
PROMETHEUS_CONSULTANT_PROVIDER_MODEL=anthropic/claude-3-5-sonnet-latest
PROMETHEUS_REVIEW_PROVIDER_MODEL=anthropic/claude-3-5-sonnet-latest
PROMETHEUS_UTILITY_PROVIDER_MODEL=anthropic/claude-3-haiku-20240307
```

## Documentation

- [Consultant Mode](CONSULTANT_MODE.md)
- [Usage Guide](USAGE_GUIDE.md)
- [Installation Guide](INSTALL.md)
- [System Architecture](SYSTEM_ARCHITECTURE.md)
- [Agent Abilities](AGENT_ABILITIES.md)
- [Hardware Specs](HARDWARE_SPECS.md)
- [Honest Abilities](HONEST_ABILITIES.md)
- [API Orchestration](API_ORCHESTRATION.md)
- [Development Log](PROMETHEUS_LOG.md)

## Current reality

Agent Prometheus is an open-source automation runtime under active hardening. It should be treated as a serious local/VPS tool, not a magical autonomous employee. The safest production path is evidence collection, human approval, then patch application.
