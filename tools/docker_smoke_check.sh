#!/usr/bin/env sh
set -eu

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.core.yml}"
APP_NAME="${APP_NAME:-Workspace Runtime}"
VITE_API_BASE="${VITE_API_BASE:-http://localhost:8000}"
VITE_WS_BASE="${VITE_WS_BASE:-ws://localhost:8000}"
export APP_NAME VITE_API_BASE VITE_WS_BASE
export REAL_API_KEY="${REAL_API_KEY:-placeholder}"
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-placeholder}"
export GEMINI_API_KEY="${GEMINI_API_KEY:-placeholder}"
export TELEGRAM_TOKEN="${TELEGRAM_TOKEN:-placeholder}"
export TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-0}"
export VPS_PUBLIC_IP="${VPS_PUBLIC_IP:-127.0.0.1}"

cleanup() {
  docker compose -f "$COMPOSE_FILE" down --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

echo "[docker-smoke] Validating compose syntax: $COMPOSE_FILE"
docker compose -f "$COMPOSE_FILE" config >/tmp/runtime-compose.yml

echo "[docker-smoke] Building core runtime images"
docker compose -f "$COMPOSE_FILE" build backend prometheus-orchestrator prometheus-frontdesk vision-bridge

echo "[docker-smoke] Starting Redis and backend"
docker compose -f "$COMPOSE_FILE" up -d redis backend

echo "[docker-smoke] Waiting for backend health"
for i in $(seq 1 60); do
  if docker compose -f "$COMPOSE_FILE" exec -T backend python - <<'PY'
import json
import urllib.request
payload = json.load(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3))
assert payload.get('status') == 'ok', payload
print(payload)
PY
  then
    break
  fi
  if [ "$i" = "60" ]; then
    echo "[docker-smoke] Backend did not become healthy"
    docker compose -f "$COMPOSE_FILE" logs --tail=120 backend redis
    exit 1
  fi
  sleep 2
done

echo "[docker-smoke] Checking runtime routes"
docker compose -f "$COMPOSE_FILE" exec -T backend python - <<'PY'
import json
import urllib.request
routes = json.load(urllib.request.urlopen('http://127.0.0.1:8000/runtime/routes', timeout=3))
paths = {route['path'] for route in routes}
required = {'/health', '/stats', '/queue', '/notifications', '/approvals', '/tasks', '/reports'}
missing = sorted(required - paths)
assert not missing, missing
print({'route_count': len(paths), 'required_routes': sorted(required)})
PY

echo "[docker-smoke] Queueing smoke task"
docker compose -f "$COMPOSE_FILE" exec -T backend python - <<'PY'
import json
import urllib.request
request = urllib.request.Request(
    'http://127.0.0.1:8000/tasks',
    data=json.dumps({'task': 'SMOKE: confirm backend queue wiring only'}).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST',
)
payload = json.load(urllib.request.urlopen(request, timeout=3))
assert payload.get('queued') is True, payload
print(payload)
PY

echo "[docker-smoke] Smoke check passed"
