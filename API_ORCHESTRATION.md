# Prometheus: The Tiered Switchboard (API Orchestration)

To prevent the "Frankenstein" stack from burning through your budget, Agent Prometheus uses a **Tiered Switchboard** architecture via the LiteLLM Gateway.

## 1. The Switchboard (config.yaml)
LiteLLM intercepts every agent request and routes it to the most cost-effective model based on the agent's specific role.

### Model Tiers:
| Role | Alias | Recommended Model | Use Case |
| :--- | :--- | :--- | :--- |
| **Orchestrator** | `orchestrator-model` | Claude 3.5 Sonnet | Logic, QA, Delegation |
| **Specialist** | `coding-model` | Claude 3.5 Sonnet | Hard coding & debugging |
| **Scout** | `research-model` | Gemini 1.5 Flash | High-volume web research |
| **Utility** | `utility-model` | GPT-4o-Mini | Scaffolding, Summarizing |

## 2. Token Saving Architecture (V3)

### **A. Global Prompt Caching (The 90% Discount)**
Agents repeatedly send massive system prompts (10k+ tokens) on every loop. By enabling Redis-based caching in the LiteLLM gateway, we stop paying for these redundant tokens.
- **Enabled in:** `config/litellm_config.yaml`
- **Requirement:** A running Redis instance.

### **B. The $5.00 Kill-Switch**
To prevent AutoGPT or other agents from entering a "Reasoning Death Spiral," the gateway enforces a hard budget cap:
```yaml
litellm_settings:
  max_budget: 5.00 # Kill session if cost exceeds $5
```

### **C. Standardized Logging**
We use `success_callback: ["langfuse"]` to monitor exactly which agent is consuming the most resources, allowing us to swap their backend model if they become too expensive.

## 3. Implementation (The "Hijack")
We don't rewrite the sub-frameworks. We simply "hijack" their connection via environment variables in the central `.env`:

```bash
# Force OpenHands to talk to the local switchboard via the Docker host bridge
# For Mac/Windows (Docker Desktop):
OPENHANDS_OPENAI_API_BASE=http://host.docker.internal:4000
# For Linux Native Docker:
# OPENHANDS_OPENAI_API_BASE=http://172.17.0.1:4000

OPENHANDS_OPENAI_MODEL_NAME=coding-model

# Force AutoGPT to use the economy model
AUTOGPT_OPENAI_API_BASE=http://host.docker.internal:4000
AUTOGPT_OPENAI_MODEL_NAME=research-model
```
