#!/usr/bin/env bash
set -euo pipefail

printf '%s\n' 'Initializing Agent Prometheus...'

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1"
    exit 1
  }
}

need_cmd docker
need_cmd python3
need_cmd curl

if docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
else
  echo 'Docker Compose is required.'
  exit 1
fi

DETECTED_IP="${VPS_PUBLIC_IP:-}"
if [ -z "$DETECTED_IP" ]; then
  DETECTED_IP="$(curl -s --connect-timeout 2 ifconfig.me || true)"
fi
DETECTED_IP="${DETECTED_IP:-YOUR_VPS_IP}"

if [ ! -f .env ]; then
  cat > .env <<EOF
# Provider-neutral consultant mode.
# Pick any LiteLLM-supported model. Cheap/weak models work best when PROMETHEUS_AUTO_APPLY=false.
PROMETHEUS_CONSULTANT_PROVIDER_MODEL=groq/llama-3.1-8b-instant
PROMETHEUS_REVIEW_PROVIDER_MODEL=groq/llama-3.1-8b-instant
PROMETHEUS_UTILITY_PROVIDER_MODEL=groq/llama-3.1-8b-instant
PROMETHEUS_CONSULTANT_API_KEY=
PROMETHEUS_REVIEW_API_KEY=
PROMETHEUS_UTILITY_API_KEY=

OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=
REAL_API_KEY=

MODEL_PROFILE=consultant
LITELLM_MASTER_KEY=sk-prometheus-local
PROMETHEUS_AUTO_APPLY=false
PROMETHEUS_MAX_FILES=120
PROMETHEUS_MAX_FILE_CHARS=6000
PROMETHEUS_EVIDENCE_BUDGET=28000
PROMETHEUS_APPROVAL_TIMEOUT=1800
PROMETHEUS_TASK_TIMEOUT=900

TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=

REDIS_HOST=redis
CHROMA_HOST=chromadb
VPS_PUBLIC_IP=$DETECTED_IP
EOF
  echo 'Created .env. Edit API keys before starting the stack.'
else
  grep -q '^PROMETHEUS_CONSULTANT_PROVIDER_MODEL=' .env || echo 'PROMETHEUS_CONSULTANT_PROVIDER_MODEL=groq/llama-3.1-8b-instant' >> .env
  grep -q '^PROMETHEUS_CONSULTANT_API_KEY=' .env || echo 'PROMETHEUS_CONSULTANT_API_KEY=' >> .env
  grep -q '^PROMETHEUS_AUTO_APPLY=' .env || echo 'PROMETHEUS_AUTO_APPLY=false' >> .env
  grep -q '^MODEL_PROFILE=' .env || echo 'MODEL_PROFILE=consultant' >> .env
  grep -q '^LITELLM_MASTER_KEY=' .env || echo 'LITELLM_MASTER_KEY=sk-prometheus-local' >> .env
fi

mkdir -p workspace/hive_mind_db workspace/research workspace/staging workspace/production workspace/artifacts workspace/logs
touch .prometheusignore
chmod -R u+rwX,g+rwX workspace

python3 -m venv venv
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ -f dashboard/package.json ]; then
  (cd dashboard && npm install)
fi

"${COMPOSE[@]}" pull || true
"${COMPOSE[@]}" build

echo 'Setup complete.'
echo "Start with: ${COMPOSE[*]} up -d"
echo 'Dashboard: http://localhost:5173'
echo 'Backend health: http://localhost:8000/health'
