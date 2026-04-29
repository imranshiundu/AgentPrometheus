# Agent Prometheus Consultant Mode

Agent Prometheus should not depend on a powerful model pretending to be an operating system. The runtime should behave like a real operating system, while the AI behaves like a consultant.

## Core rule

```text
The system executes. The model advises.
```

The runtime is responsible for scanning repositories, building a repo map, selecting relevant files, reading files safely, running deterministic checks, collecting logs, maintaining task state, preparing compact evidence packets, applying approved patches, and producing reports.

The AI model is responsible for interpreting evidence, identifying likely causes, proposing small patch operations, warning about risk, asking for missing evidence, and reviewing post-patch results.

The model must never claim that a test passed unless the runtime supplied the test output.

## Why this works with weak models

Weak or cheap models fail when they are asked to hold the whole project in memory and invent an execution path. Consultant Mode avoids that.

Instead of asking the model to inspect the whole world, Prometheus sends a compact JSON evidence packet with the task, repo map, selected files, compile errors, known logs, and constraints. The model replies with strict JSON. This makes lower-reasoning models usable because the response shape is simple and the context is already prepared.

## Safety stance

By default:

```env
PROMETHEUS_AUTO_APPLY=false
```

That means the model may propose patches, but the runtime reports them for approval before writing files. This is safer for Groq-small, local models, and any weak model.

For trusted local workflows, automatic patching can be enabled:

```env
PROMETHEUS_AUTO_APPLY=true
```

Do not enable auto-apply on public servers or unknown repositories until tests, backups, and rollback gates exist.

## Recommended model profile variables

```env
PROMETHEUS_CONSULTANT_MODEL=consultant-model
PROMETHEUS_CHEAP_MODEL=utility-model
PROMETHEUS_CONSULTANT_PROVIDER_MODEL=groq/llama-3.1-8b-instant
PROMETHEUS_REVIEW_PROVIDER_MODEL=groq/llama-3.1-8b-instant
PROMETHEUS_UTILITY_PROVIDER_MODEL=groq/llama-3.1-8b-instant
OPENAI_API_BASE=http://litellm:4000/v1
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
- `setup.sh` creates a safe environment template for consultant-first operation.
