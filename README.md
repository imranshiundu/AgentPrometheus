# Agent Prometheus: The Titan-Class AI Orchestrator (V2)

![Agent Prometheus Logo](logo.png)

Agent Prometheus is a hierarchical Multi-Agent System (MAS) that unifies the specialized capabilities of **AutoGPT, OpenHands, crewAI, and gpt-engineer**. 

In its V2 evolution, Prometheus has moved from a "Framework Integration" model to a **"Modular Tool Intelligence"** model, drastically reducing token consumption and architecture bloat.

---

## 🔱 V3 Evolution: Microservices & SSoT

Agent Prometheus has evolved from basic integration to a **Microservices-Based Agent Architecture**. This preserves the "magic" of framework-specific reasoning loops while enforcing a **Single Source of Truth (SSoT)**.

### 1. Spec-Driven Development
Prometheus no longer codes from generic prompts. The process is now strictly controlled:
- **Phase 1: Spec Generation:** The Architect generates a strict `SPEC.md`.
- **Phase 2: TDD Preparation:** The Architect generates failing tests *before* coding begins.
- **Phase 3: Service Execution:** specialized frameworks (OpenHands, AutoGPT) are treated as **APIs**, preserving their internal brilliance.
- **Phase 4: The Spec Guardian:** A QA agent audits all work against the `SPEC.md`. If a feature is "Out-of-Scope," it is rejected.

### 2. Architecture Comparison
![Microservices Architecture](microservices_architecture.png)
Prometheus utilizes a Microservices-style approach (left) to ensure failure in one agent doesn't bring down the Titan.

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
