# Agent Prometheus

Agent Prometheus is an experimental open-source multi-agent automation system.

The safer direction for this project is consultant-mode automation:

The system executes. The AI consults.

This means Prometheus should scan files, collect evidence, queue tasks, run checks, keep logs, and ask an LLM for structured advice. The LLM should not be treated as an all-knowing commander. This makes the system safer and cheaper, especially when using small or fast models such as Groq-hosted models.

## Current Status

This repository is under active hardening. The main branch still contains the original multi-agent framework structure, while newer consultant-mode work is being tested in branches and pull requests.

Branches currently visible:

- main
- consultant-runtime-groq-clean
- prometheus-hardening-runtime-upgrade
- consultant-runtime-final-safe

Do not blindly merge branches without testing. The safe path is to test one branch at a time, confirm Docker boots, then merge.

## What Prometheus Is Supposed To Do

Prometheus is intended to receive tasks through Telegram or a dashboard, store task state in Redis, keep project memory in ChromaDB, route model calls through LiteLLM, use provider-neutral model aliases, send small evidence packets to the model, request approval before risky edits, and support Groq or other OpenAI-compatible providers through LiteLLM.

## Recommended Architecture

Telegram or dashboard sends a task to Redis. The Prometheus runtime collects evidence, runs safety checks, sends a small packet to a LiteLLM model alias, receives structured consultant advice, then the runtime decides what to do next.

The model should be used for summarising evidence, planning, reviewing code, identifying risks, proposing patches, and explaining failures.

The runtime should handle file scanning, logs, execution, command running, approvals, tests, saving outputs, and rollback rules.

## Minimum Requirements

For a small local test:

- CPU: 2 cores
- RAM: 4 GB minimum
- Disk: 10 GB free
- OS: Ubuntu 22.04/24.04, Debian, macOS, or WSL2
- Python: 3.11 recommended
- Node.js: 18+
- Docker: latest stable
- Docker Compose: v2 recommended

This can boot the light parts of the stack, but it may struggle if OpenHands or heavy browser automation is enabled.

## Recommended Requirements

For a usable developer setup:

- CPU: 4 cores or more
- RAM: 8 GB minimum, 16 GB better
- Disk: 30 GB free
- OS: Ubuntu 24.04 LTS recommended
- Python: 3.11
- Node.js: 18 or 20
- Docker Engine and Docker Compose v2
- Stable internet connection

For a VPS, use 2 vCPU and 4 GB RAM for a basic Telegram, Redis, and LiteLLM setup. Use 4 vCPU and 8 GB RAM for a stable always-on setup. Use 8 vCPU and 16 GB RAM if running heavier sandboxes, browser automation, or OpenHands-like services.

## API Requirements

At least one model provider key is required. For the Groq-first direction, add a Groq API key in the environment and point LiteLLM model aliases to Groq models.

Optional providers include OpenAI, Anthropic, Gemini, or any provider supported by LiteLLM.

Telegram is optional, but needed for remote command mode.

## Install

Run setup.sh, then edit .env and add your real keys.

## Run

Use Docker Compose to build and start the system. Then check running containers and logs.

## Safety Defaults

Prometheus should keep automatic file editing disabled by default. This means the model may propose changes, but the runtime should not blindly apply them. This is especially important when using small models. Weak models can be useful when they receive small, clean evidence packets, but they should not be trusted with full autonomous control.

## Testing Checklist Before Merging Branches

Before merging any hardening branch into main, run Python compile checks, validate Docker Compose, build the containers, inspect container status, and review recent logs. If the backend exposes a health endpoint, test it locally. If using Telegram, send /start and confirm that messages are received.

## Known Limitations

- The project is still experimental.
- Some branches are ahead of main and need careful review before merging.
- Full Docker integration testing must be done on a real machine or VPS.
- AI providers may return inconsistent output unless prompts are strict and evidence packets are small.
- Automatic code editing should remain disabled until the runtime has strong test and rollback gates.

## Repository Documents

- Usage Guide: USAGE_GUIDE.md
- Remote Control: REMOTE_CONTROL.md
- Installation Guide: INSTALL.md
- System Architecture: SYSTEM_ARCHITECTURE.md
- Agent Abilities: AGENT_ABILITIES.md
- Hardware Specs: HARDWARE_SPECS.md
- Honest Abilities: HONEST_ABILITIES.md
- API Orchestration: API_ORCHESTRATION.md
- Development Log: PROMETHEUS_LOG.md

## Development Rule

Do not market Prometheus as uncrashable or fully autonomous until the tests prove it. The project should be honest: it is a local-first automation runtime that uses AI as a consultant layer.
