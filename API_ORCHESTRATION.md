# Agent Prometheus: API Orchestration & Key Management

As a Senior Developer, ensuring cost-efficiency and security while managing four massive AI frameworks is paramount. This document defines how we unify these frameworks under a single API key identity.

## 1. The Single Identity Principle
Each framework (AutoGPT, OpenHands, crewAI, gpt-engineer) was originally designed to consume its own `OPENAI_API_KEY`. To simplify this and allow for centralized monitoring, we use **LiteLLM Proxy** as our Unified Gateway.

## 2. Infrastructure Setup

### Gateway Architecture
Instead of providing the actual API key to each container/process, we provide a local mock endpoint:

1.  **Orchestrator Level:** A single master `.env` file contains the `REAL_API_KEY`.
2.  **Proxy Level:** LiteLLM starts as a service, consuming the `REAL_API_KEY`. It exposes a local endpoint: `http://localhost:4000/v1`.
3.  **Client Level:** All frameworks are configured with:
    - `OPENAI_API_BASE=http://localhost:4000/v1`
    - `OPENAI_API_KEY=sk-hybrid-orchestrator-key` (a dummy key)

## 3. Configuration Breakdown

### LiteLLM Mapping (`config.yaml`)
```yaml
model_list:
  - model_name: gpt-4
    litellm_params:
      model: openai/gpt-4
      api_key: "os.environ/REAL_API_KEY"
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: openai/gpt-3.5-turbo
      api_key: "os.environ/REAL_API_KEY"
```

### Framework-Specific Injection
- **crewAI:** Uses `LLM(model="gpt-4", base_url="http://localhost:4000/v1")`.
- **OpenHands:** Injected via `config.toml` under `[llm]` section.
- **AutoGPT:** Configured in `.env` under `OPENAI_API_BASE`.
- **gpt-engineer:** Passed via environment variable `OPENAI_API_BASE`.

## 4. Key Benefits
1. **Budget Capping:** We can set a hard limit at the LiteLLM level. If the "AutoGPT" loop goes rogue and spends $10, the proxy shuts down the connection for all agents.
2. **Unified Observability:** Every single token spent by any framework is logged in one place. We can see exactly which "agent" (Research vs Coding) is consuming the most resources.
3. **Provider Agnostic:** If we want to switch from OpenAI to Anthropic, we only change the `config.yaml` in the Proxy. The four frameworks never even know the backend changed.

## 5. Security Guardrails
- **Key Rotation:** One-click rotation at the proxy level.
- **Access Control:** Only the internal Docker network can reach the LiteLLM Proxy. No external traffic can spoof requests using the proxy.
