# Agent Prometheus: The Titan-Class AI Orchestrator

Agent Prometheus is a hierarchical Multi-Agent System (MAS) that unifies **AutoGPT, OpenHands, crewAI, and gpt-engineer** into a single, cohesive entity. It brings the "fire" of autonomous research and specialized coding to your local environment through a central cognitive core.

## 🛠 Prerequisites

Regardless of your Operating System, ensure the following are installed:

- **Git** (for version control)
- **Docker & Docker Compose** (Recommended for isolation)
- **Python 3.10 or higher** (If running natively)
- **OpenAI API Key** (A single key is used via the LiteLLM Gateway)

---

## 🚀 Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/imranshiundu/AgentPrometheus.git
cd AgentPrometheus
```

### 2. Environment Configuration
Create a `.env` file in the root directory:
```bash
# General
REAL_API_KEY=your_openai_api_key_here

# Optional: Docker settings
DOCKER_DEFAULT_PLATFORM=linux/amd64
```

### 3. Deployment Method

#### Option A: Docker (Recommended - All OS)
*Best for avoiding dependency conflicts across frameworks.*
```bash
docker-compose up -d
```

#### Option B: Linux/macOS Native
```bash
python3 -m venv venv
source venv/bin/activate
pip install crewai langchain-openai litellm python-dotenv
```

#### Option C: Windows Native (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install crewai langchain-openai litellm python-dotenv
```

---

## 🏗 System Architecture & Specs

### Agent Ability Matrix
| Agent | Role | Capability | Powered By |
| :--- | :--- | :--- | :--- |
| **Architect (Titan)** | Structural Design | Project Scaffolding | gpt-engineer |
| **Specialist (Hephaestus)** | Core Development | Coding & Sandboxed Debugging | OpenHands |
| **Scout (Hermes)** | Intelligence | Autonomous Web Research | AutoGPT |
| **Orchestrator** | Management | Delegation & QA | crewAI |

### Technical Specifications
- **Orchestration:** crewAI (Hierarchical & Sequential processes)
- **LLM Proxy:** LiteLLM (Unified cost control & monitoring)
- **Database/Workspace:** Shared local volume mount (`/shared_workspace`)
- **Network:** Isolated Docker Bridge for inter-agent communication

---

## 📖 Operational Documentation
- [System Architecture](SYSTEM_ARCHITECTURE.md) - Deep dive into the execution lifecycle.
- [Agent Abilities](AGENT_ABILITIES.md) - Specialized superpowers of each framework.
- [API Orchestration](API_ORCHESTRATION.md) - Detailed guide on the single-key setup.
- [Development Log](PROMETHEUS_LOG.md) - Changelog and technical decisions.

## 🧹 Maintenance
To clean up shared workspace artifacts:
```bash
rm -rf shared_workspace/*
```

---

## 🛡 License
This project is open-source. See the individual sub-directory licenses for AutoGPT, OpenHands, and crewAI specific terms.
