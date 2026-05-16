# Agent Prometheus Cleanup Map

This document controls public naming and safe folder cleanup.

## Public Naming Rule

Use **Agent Prometheus** as the system name everywhere visible to users, contributors, README readers, dashboards, and setup guides.

Do not present upstream projects as separate public products inside this repository. Upstream names may appear only as implementation notes, adapters, or inspiration.

## Current Safe Runtime Names

| Current Path / Name | Public Name | Status |
|---|---|---|
| `dashboard/` | Command Center | Keep path for now; rename later only with full Compose + CI update |
| `backend/` | Runtime API | Keep path for now; already wired in Compose |
| `config/` | Model Gateway Config | Keep path; low-risk internal name |
| `tools/` | Runtime Tools | Keep path; low-risk internal name |
| `workspace/` | Workspace | Keep path; mounted by Compose and runtime |
| `prometheus_consultant.py` | Consultant Runtime | Primary production entrypoint |
| `prometheus_indexer.py` | Evidence Indexer | Maintained |
| `prometheus_json.py` | Response Normalizer | Maintained |
| `telegram_gateway.py` | Telegram Gateway | Maintained |
| `memory_ledger.py` | Runtime Memory Ledger | Maintained |
| `prometheus_manager.py` | Legacy Orchestration Experiment | Do not use as production entrypoint |

## Deferred Physical Renames

These renames are desirable but should be done only when the repository tree can be fully enumerated and every reference can be updated in the same commit.

| Proposed Rename | Reason |
|---|---|
| `dashboard/` -> `command-center/` | Better public naming, but Docker Compose, Vite paths, docs, and CI must move together |
| `backend/` -> `runtime-api/` | Better public naming, but Compose and CI currently depend on `backend/src/main.py` |
| `config/` -> `model-gateway/` | Optional; current name is acceptable and not user-hostile |

## Deletion Policy

Delete old sub-agent documentation only when the exact file exists and its content has been merged into the main README or docs.

Do not delete unreadable or unverified folders blindly.

## Legacy Language Replacement

Prefer these replacements in user-facing files:

| Avoid | Use |
|---|---|
| AutoGPT agent | Prometheus workflow runtime |
| OpenHands agent | Optional sandbox adapter |
| CrewAI team | Legacy orchestration experiment |
| GPT Engineer clone | Spec-to-code inspiration |
| Hive Mind as product name | Runtime Memory |
| Scout / Specialist / CEO in UI | Evidence Scanner / Consultant Runtime / Patch Gate |

## Next Safe Cleanup Steps

1. keep production entrypoint on `prometheus_consultant.py`
2. keep Compose and CI aligned
3. remove stale public wording from UI and README
4. add explicit docs for runtime API and dashboard API contract
5. only physically rename folders after a complete tree listing is available
