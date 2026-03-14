#!/bin/bash

# Agent Prometheus Setup Script (Linux/Mac)
# "Forging the Titan"

echo "🔱 Initializing the Agent Prometheus Forge..."

# 1. Dependency Checks
command -v docker >/dev/null 2>&1 || { echo >&2 "❌ Docker is required but not installed. Aborting."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo >&2 "❌ Docker Compose is required but not installed. Aborting."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo >&2 "❌ Python 3 is required but not installed. Aborting."; exit 1; }

# 2. Environment Setup
if [ ! -f .env ]; then
    echo "⚙️ Creating .env from template..."
    cat <<EOF > .env
# --- API KEYS ---
REAL_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIzaSy...

# --- TELEGRAM CONFIG ---
TELEGRAM_TOKEN=...
TELEGRAM_CHAT_ID=...

# --- INFRASTRUCTURE ---
REDIS_HOST=localhost
EOF
    echo "⚠️  Please update the .env file with your actual API keys and Telegram credentials."
fi

# 3. Directory Preparation
echo "📁 Preparing shared workspace..."
mkdir -p shared_workspace/hive_mind_db
mkdir -p workspace

# 4. Python Environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Docker Infrastructure
echo "🐳 Pulling Docker infrastructure..."
docker-compose pull

echo "✅ Setup Complete. Agent Prometheus is ready for its first command."
echo "👉 To start: 'docker-compose up -d' followed by 'python telegram_gateway.py'"
