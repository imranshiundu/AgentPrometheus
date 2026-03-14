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
    # Attempt to auto-detect VPS IP for vision node convenience
    DETECTED_IP=$(curl -s --connect-timeout 2 ifconfig.me || echo "YOUR_VPS_IP")
    
    cat <<EOF > .env
# --- API KEYS ---
REAL_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIzaSy...

# --- TELEGRAM CONFIG ---
TELEGRAM_TOKEN=...
TELEGRAM_CHAT_ID=...

# --- INFRASTRUCTURE ---
REDIS_HOST=redis
CHROMA_HOST=chromadb
VPS_PUBLIC_IP=$DETECTED_IP
EOF
    echo "⚠️ Created .env template. Please edit it with your real keys and Telegram credentials."
fi

# 3. Directory Preparation
echo "📁 Preparing local workspace..."
mkdir -p workspace/hive_mind_db
mkdir -p workspace/research
mkdir -p workspace/staging
mkdir -p workspace/production
mkdir -p config dashboard docker backend
touch .prometheusignore

# Set Permissions (Ensure Docker doesn't lock the workspace as root)
chmod -R 777 workspace/

# 4. Python Environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install crewai langchain-openai redis python-dotenv python-telegram-bot chromadb mss pyautogui websockets openai

# 5. Dashboard Setup
if [ -d "dashboard" ]; then
    echo "⚛️ Setting up Web Dashboard..."
    cd dashboard && npm install && cd ..
fi

# 6. Docker Infrastructure
echo "🐳 Pulling Docker infrastructure..."
docker-compose pull

echo "✅ Setup Complete. Agent Prometheus is ready for its first command."
echo "👉 To start:"
echo "   1. docker-compose up -d"
echo "   2. python telegram_gateway.py"
echo "   3. (In separate shell) python prometheus_manager.py"
echo "👉 Then open Telegram and type /start"
