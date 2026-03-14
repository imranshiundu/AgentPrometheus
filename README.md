# Agent Prometheus: The Titan-Class AI Orchestrator (V2)

![Agent Prometheus Logo](logo.png)

Agent Prometheus is a hierarchical Multi-Agent System (MAS) that unifies the specialized capabilities of **AutoGPT, OpenHands, crewAI, and gpt-engineer**. 

In its V2 evolution, Prometheus has moved from a "Framework Integration" model to a **"Modular Tool Intelligence"** model, drastically reducing token consumption and architecture bloat.

---

## ⚡ V2 Optimizations (Efficiency & Stability)

### 1. Tiered Intelligence Routing
Prometheus no longer uses expensive models for every task. We route traffic through the **LiteLLM Gateway** based on specific agent needs:
- **High Reasoning (Manager/QA):** GPT-4o or Claude 3.5 Sonnet.
- **Precision (Coding):** Claude 3.5 Sonnet (Best-in-class syntax).
- **Utility (Research/Refining):** Gemini 1.5 Flash or GPT-4o-Mini (Extreme cost savings).

### 2. The Refiner Agent (Token Caching)
We have introduced a **"Refiner"** agent between every handover. This agent's only role is to compress the outputs in the shared workspace into strict JSON or concise bullet points, preventing the "Telephone Game" context window bloat.

### 3. Loop Guardrails & Timeouts
Every Titan (Architect, Specialist, Scout) now has a hard-coded `max_iter` limit (typically 5 iterations). This prevents the system from getting stuck in infinite "research loops" that burn API credits.

### 4. Shared Memory Layer
Prometheus now utilizes a `global_state.json` inside the shared workspace to maintain a persistent state of the project, ensuring that reasoning context isn't lost when switching between different framework modules.

---

## 🏗 System Architecture & Specs

### Agent Ability Matrix
| Agent | Role | LLM Tier | Primary Framework |
| :--- | :--- | :--- | :--- |
| **Architect (Titan)** | Structural Design | Economy | gpt-engineer |
| **Specialist (Hephaestus)** | Execution | Precision | OpenHands |
| **Scout (Hermes)** | Intelligence | Economy | AutoGPT |
| **Refiner** | Optimization | Economy | Integration Logic |
| **Orchestrator** | Management | High-Reasoning | crewAI (Manager) |

---

## 🚀 Setup Instructions

### 1. Environment Configuration
Create a `.env` file in the root directory:
```bash
# Providers (Only fill what you use)
REAL_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GEMINI_API_KEY=your_gemini_key
```

### 2. Launch Infrastructure
```bash
docker-compose up -d
```
*Note: V2 enables **Prompt Caching** by default via LiteLLM to reduce costs for repetitive system prompts.*

---

## 📖 Operational Documentation
- [System Architecture](SYSTEM_ARCHITECTURE.md) - Deep dive into the V2 execution lifecycle.
- [Agent Abilities](AGENT_ABILITIES.md) - Updated for the new "Refiner" and "Summarizer" roles.
- [API Orchestration](API_ORCHESTRATION.md) - Guide to the Tiered Routing and LiteLLM Proxy.
- [Development Log](PROMETHEUS_LOG.md) - The chronicle of the V2 refactor.

## 🧹 Maintenance
To reset the global state and workspace:
```bash
rm -rf shared_workspace/*
```

---

## 🛡 License
This project is open-source. Forged for builders who want the power of all agents with the cost of only one.
