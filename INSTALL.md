# Installation Guide: Agent Prometheus 🔱

Follow these instructions to forge Agent Prometheus on your machine. This guide covers Linux, macOS, and Windows (via WSL2).

---

## 🛠 Prerequisites

Before starting, ensure you have the following installed:
1.  **Docker & Docker Compose** (Required for sandboxed execution).
2.  **Python 3.10 or higher**.
3.  **Git**.
4.  **A Telegram Bot Token** (Get this from [@BotFather](https://t.me/botfather)).
5.  **Your Telegram Chat ID** (Get this from [@userinfobot](https://t.me/userinfobot)).
    > [!IMPORTANT]
    > **SECURITY CRITICAL:** You MUST enter your specific Telegram `CHAT_ID` in the `.env` file. The Gateway will hard-reject any commands from unauthorized IDs to prevent remote code execution attacks from strangers.

---

## 🐧 Linux (Ubuntu/Debian)

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/imranshiundu/AgentPrometheus.git
    cd AgentPrometheus
    ```

2.  **Run the Setup Script:**
    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```

3.  **Configure Environment:**
    Open the `.env` file and enter your API keys and Telegram credentials.

4.  **Launch:**
    ```bash
    docker-compose up -d
    source venv/bin/activate
    python telegram_gateway.py
    ```

---

## 🍎 macOS (M-Series / Intel)

1.  **Clone & Setup:**
    Open Terminal and run:
    ```bash
    git clone https://github.com/imranshiundu/AgentPrometheus.git
    cd AgentPrometheus
    chmod +x setup.sh
    ./setup.sh
    ```

2.  **Docker Desktop:**
    Ensure **Docker Desktop** is running.

3.  **Launch:**
    ```bash
    docker-compose up -d
    source venv/bin/activate
    python telegram_gateway.py
    ```

---

## 🪟 Windows (WSL2)

> [!IMPORTANT]
> Agent Prometheus **MUST** be run inside WSL2 (Ubuntu). Do not attempt to run it natively on Windows CMD or PowerShell.

1.  **Initialize WSL2:**
    Open your Ubuntu terminal in WSL2.

2.  **Clone & Setup:**
    ```bash
    git clone https://github.com/imranshiundu/AgentPrometheus.git
    cd AgentPrometheus
    chmod +x setup.sh
    ./setup.sh
    ```

3.  **Docker Integration:**
    Ensure Docker Desktop for Windows has "WSL2 Integration" enabled for your Ubuntu distribution.

4.  **Launch:**
    Follow the same launch commands as Linux.

---

## 🚀 Post-Installation Check

Once the `telegram_gateway.py` is running, open Telegram and send `/start` to your bot. If it replies with "🔱 Agent Prometheus Online," you have successfully forged the Titan.

---

## 🧹 Maintenance & Resets

To stop everything and wipe the temporary workspace:
```bash
docker-compose down
rm -rf workspace/*
```
