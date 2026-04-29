# Upstream Agent Feature Map

Agent Prometheus is not a copy of AutoGPT, OpenHands, CrewAI, or GPT Engineer. It uses their strongest public design lessons as inspiration while keeping its own architecture: evidence-first runtime, consultant-model reasoning, safety gates, and developer-controlled execution.

This document tracks what Prometheus should learn from the wider open-source agent ecosystem and how those ideas should be implemented safely.

## Source projects to watch

| Project | Repository | What to study | Prometheus interpretation |
|---|---|---|---|
| AutoGPT | `Significant-Gravitas/AutoGPT` | continuous agents, agent builder, workflows, marketplace, frontend, benchmarking, Agent Protocol | build workflow blocks, benchmark harness, agent protocol adapter, dashboard lifecycle controls |
| OpenHands | `All-Hands-AI/OpenHands` | software-engineering agent UX, workspace/sandbox control, terminal/browser/file operations | build a controlled developer workspace, command policy, patch review, execution sandbox |
| CrewAI | `crewAIInc/crewAI` | Crews, Flows, roles, tasks, event-driven orchestration, control plane concepts | add Prometheus crews and deterministic flows without making the model the executor |
| GPT Engineer | `gpt-engineer-org/gpt-engineer` | spec-to-code planning, file generation, clarification loop, project scaffolding | add build-from-spec mode with planning, file tree proposal, patch batches, and verification loops |

## Feature families Prometheus should own

### 1. Workflow blocks inspired by AutoGPT

Prometheus should support reusable blocks such as:

- research block
- repo scan block
- file evidence block
- test runner block
- patch proposal block
- approval block
- report block
- notification block
- GitHub issue/PR block

Rules:

- every block must declare inputs and outputs
- every block must declare whether it reads, writes, executes, or sends data outside the machine
- blocks must be deterministic where possible
- model calls should be explicit blocks, not hidden side effects

### 2. Developer workspace inspired by OpenHands

Prometheus should grow toward a serious coding workspace:

- file browser
- diff viewer
- terminal command queue
- command approval policy
- logs panel
- task timeline
- patch review panel
- rollback snapshots

Rules:

- commands must be policy-checked before execution
- risky commands require approval
- workspace writes must be logged
- test results must come from actual runtime output, not model claims

### 3. Crews and flows inspired by CrewAI

Prometheus should support role-based agents, but runtime-owned orchestration remains the rule.

Example roles:

- Researcher
- Architect
- Security Reviewer
- Code Editor
- Test Runner
- Documentation Writer
- Release Manager

Example flow:

```text
research -> architecture -> patch proposal -> safety review -> approval -> apply -> test -> report
```

Rules:

- agents are roles, not uncontrolled processes
- flows are state machines controlled by Prometheus
- each step must produce structured output
- failed steps must stop or route to review

### 4. Spec-to-code mode inspired by GPT Engineer

Prometheus should support a build mode that starts with a product or engineering spec.

Flow:

```text
spec intake -> clarification questions -> architecture plan -> file tree proposal -> patch batches -> tests -> documentation -> release notes
```

Rules:

- no broad rewrite without a plan
- generated file trees must be shown before write
- patches should be small enough to review
- tests must be created or updated with code

### 5. Benchmarking inspired by AutoGPT/agbenchmark

Prometheus should gain its own benchmark suite:

- README review task
- Python bugfix task
- Docker Compose diagnosis task
- missing-env detection task
- documentation generation task
- safe patch task
- refusal/safety task

Metrics:

- task success
- patch accuracy
- tokens used
- runtime cost
- hallucinated claims
- unsafe operation attempts
- time to useful result

## Auto-update strategy

Prometheus should not automatically copy code from upstream projects. That is unsafe technically and legally.

Instead, Prometheus should automatically watch upstream repositories and open an issue or report when they change.

Safe update loop:

```text
1. Check latest upstream commit SHA
2. Compare against stored last-seen SHA
3. Fetch release notes / README / changed paths
4. Generate a Prometheus impact report
5. Open a GitHub issue or local report
6. Human reviews whether to implement anything
7. Prometheus implements only selected ideas using original code
```

## License guardrail

Do not copy source code directly from upstream projects unless the license allows it and attribution requirements are followed. Some projects use mixed licensing. For example, parts of AutoGPT are MIT while the `autogpt_platform` folder is under Polyform Shield. Prometheus should prefer clean-room implementation of ideas over copying code.

## Implementation roadmap

### Phase 1: Watch and document

- add upstream watcher script
- add scheduled GitHub Action
- write update reports into `docs/upstream_reports/`
- document feature map

### Phase 2: Internal workflow engine

- define block schema
- define flow schema
- add block runner
- add flow runner
- add state persistence

### Phase 3: Developer workspace controls

- command policy file
- terminal command queue
- approval gate
- diff viewer data model
- rollback snapshots

### Phase 4: Multi-role crews

- role definitions
- task handoff protocol
- review chain
- model budget per role
- weak-model fallback rules

### Phase 5: Benchmarks

- create benchmark tasks
- score outputs
- track cost and token use
- publish benchmark table in README

## Prometheus principle

The target is not to become a clone of every agent framework.

The target is to become a serious open-source automation runtime that combines:

- AutoGPT-style continuous workflows
- OpenHands-style developer workspace control
- CrewAI-style role orchestration
- GPT Engineer-style spec-to-code building
- Prometheus-style evidence, safety, and weak-model reliability
