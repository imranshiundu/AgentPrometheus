# Agent Prometheus Consultant Mode

Agent Prometheus should not depend on a powerful model pretending to be an operating system. The runtime should behave like a real operating system, while the AI behaves like a consultant.

This design is inspired by the practical pattern used by modern AI workspaces: the software gathers evidence, compresses context, controls tools, and asks the model for judgement only when judgement is needed.

## Core rule

The system executes. The model advises.

The runtime is responsible for:

- scanning repositories and folders
- building a repo map
- selecting relevant files
- reading files safely
- running deterministic checks
- collecting logs and failures
- maintaining task state
- preparing compact evidence packets
- applying approved patches
- producing reports

The AI model is responsible for:

- interpreting evidence
- identifying likely causes
- proposing small patch operations
- warning about risk
- asking for missing evidence
- reviewing post-patch results

The model must never claim that a test passed unless the runtime supplied the test output.

## Why this works with weak models

Weak or cheap models fail when they are asked to hold the whole project in memory and invent an execution path. Consultant Mode avoids that.

Instead of asking the model to inspect the whole world, Prometheus sends a small JSON evidence packet:

- task
- repo map
- selected files
- compile errors
- known logs
- constraints

The model replies with strict JSON. This makes even low-reasoning models usable because the response shape is simple and the context is already prepared.

## Safety stance

By default, `PROMETHEUS_AUTO_APPLY=false`.

That means the model may propose patches, but the runtime reports them for approval before writing files. This is safer for Groq-small, local models, or any weak model.

For stronger models or local trusted workflows, `PROMETHEUS_AUTO_APPLY=true` may be enabled.

## Recommended model profiles

Cheap mode:

```env
PROMETHEUS_CONSULTANT_PROVIDER_MODEL=groq/llama-3.1-8b-instant
PROMETHEUS_REVIEW_PROVIDER_MODEL=groq/llama-3.1-8b-instant
PROMETHEUS_UTILITY_PROVIDER_MODEL=groq/llama-3.1-8b-instant
PROMETHEUS_AUTO_APPLY=false
```

Balanced mode:

```env
PROMETHEUS_CONSULTANT_PROVIDER_MODEL=groq/llama-3.1-70b-versatile
PROMETHEUS_REVIEW_PROVIDER_MODEL=groq/llama-3.1-70b-versatile
PROMETHEUS_UTILITY_PROVIDER_MODEL=groq/llama-3.1-8b-instant
PROMETHEUS_AUTO_APPLY=false
```

Premium mode:

```env
PROMETHEUS_CONSULTANT_PROVIDER_MODEL=anthropic/claude-3-5-sonnet-latest
PROMETHEUS_REVIEW_PROVIDER_MODEL=anthropic/claude-3-5-sonnet-latest
PROMETHEUS_UTILITY_PROVIDER_MODEL=anthropic/claude-3-haiku-20240307
PROMETHEUS_AUTO_APPLY=false
```

## Runtime loop

```text
1. Receive task
2. Scan workspace
3. Select relevant files
4. Run deterministic checks
5. Build evidence packet
6. Ask model for JSON plan
7. Report proposed patches
8. Apply only when approved or auto-apply is enabled
9. Re-scan and re-check
10. Produce final report
```

## Anti-hallucination rules

The consultant prompt enforces these rules:

- return JSON only
- do not invent test results
- do not mention missing files as if they exist
- request missing evidence instead of guessing
- prefer exact replace operations over broad rewrites
- keep patches small

## Current implementation files

- `prometheus_consultant.py` contains the evidence compiler, consultant call, patch validator, and task loop.
- `prometheus_manager.py` starts the consultant runtime.
- `config/litellm_config.yaml` defines provider-neutral aliases.
- `docker-compose.yml` wires Redis, LiteLLM, ChromaDB, manager, backend, Telegram front desk, and dashboard.
- `setup.sh` creates a safe `.env` for consultant-first operation.
