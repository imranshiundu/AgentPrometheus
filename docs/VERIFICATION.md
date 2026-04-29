# Agent Prometheus Verification Guide

This guide explains how to verify the repository before trusting it on a real workspace.

## 1. Source checks

Run:

```bash
python -m compileall .
python -m py_compile tools/upstream_watch.py
```

Expected result: no syntax errors.

## 2. Dependency install

Run:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Expected result: dependencies install without resolver failure.

## 3. Docker Compose configuration

Run:

```bash
docker compose config
```

Expected result: Compose prints the resolved configuration without errors.

## 4. Start services

Run:

```bash
docker compose up -d --build
docker compose ps
```

Expected result: Redis, LiteLLM, manager/runtime, and any configured supporting services start successfully.

## 5. Safe default check

Confirm `.env` contains:

```bash
PROMETHEUS_AUTO_APPLY=false
```

This keeps model-proposed patches from being written automatically.

## 6. Redis task smoke test

Push a task:

```bash
redis-cli LPUSH prometheus_tasks '{"task":"Review the README and list missing setup steps."}'
```

Then inspect logs:

```bash
docker compose logs --tail=200
```

Expected result: Prometheus picks up the task, scans the workspace, creates evidence, consults the configured model, and writes logs or notifications.

## 7. Upstream watcher check

Run:

```bash
python tools/upstream_watch.py
```

Expected result: the watcher creates or updates Markdown reports under `docs/upstream_reports/` when watched repositories have new commits.

The watcher must not copy upstream source code.

## 8. Secret hygiene

Run:

```bash
git grep -nE '(sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY)' -- . ':!README.md' ':!docs/**'
```

Expected result: no real secrets are found.

## 9. Merge readiness checklist

A PR should not be merged unless:

- Python files compile
- Docker Compose config validates
- README matches actual code
- `.env.example` is safe
- no secrets are committed
- dangerous write behavior is disabled by default
- any new feature explains what it reads, writes, executes, and sends externally
