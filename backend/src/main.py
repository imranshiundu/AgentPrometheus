import asyncio
import json
import os
from pathlib import Path
from typing import Any

import redis
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Agent Prometheus Runtime API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True, socket_connect_timeout=3, socket_timeout=3)
WORKSPACE = Path("workspace")
PRODUCTION_DIR = WORKSPACE / "production"


class TaskRequest(BaseModel):
    task: str
    chat_id: int | None = None


def parse_json(value: str | None, fallback: Any = None) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def redis_health() -> str:
    try:
        return "online" if r.ping() else "offline"
    except redis.RedisError:
        return "offline"


@app.get("/health")
async def health():
    return {"status": "ok", "redis": redis_health()}


@app.get("/vision_node.py")
async def get_vision_node():
    path = Path("vision_node.py")
    if not path.exists():
        raise HTTPException(status_code=404, detail="vision_node.py is not mounted")
    return FileResponse(path)


@app.get("/stats")
async def get_stats():
    return {
        "tokens": r.get("prometheus_token_count") or "0",
        "health": redis_health().upper(),
        "active_agents": r.get("prometheus_active_count") or "1 / 1",
        "queue_depth": r.llen("prometheus_tasks"),
        "log_count": r.llen("prometheus_logs"),
        "notification_count": r.llen("prometheus_notifications"),
        "kill_switch": r.get("prometheus_kill_switch") == "true",
        "runtime": "consultant",
    }


@app.get("/logs")
async def get_logs(limit: int = 100):
    limit = max(1, min(limit, 500))
    logs = r.lrange("prometheus_logs", 0, limit - 1)
    return [parse_json(item, {"msg": item}) for item in logs]


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            logs = r.lrange("prometheus_logs", 0, 49)
            payload = [parse_json(item, {"msg": item}) for item in logs]
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        return


@app.post("/tasks")
async def create_task(request: TaskRequest):
    task = request.task.strip()
    if not task:
        raise HTTPException(status_code=400, detail="Task cannot be empty")
    payload: dict[str, Any] = {"task": task, "source": "dashboard", "status": "queued"}
    if request.chat_id is not None:
        payload["chat_id"] = request.chat_id
    r.lpush("prometheus_tasks", json.dumps(payload))
    return {"queued": True, "queue_depth": r.llen("prometheus_tasks")}


@app.post("/control/kill-switch")
async def trigger_kill_switch():
    r.set("prometheus_kill_switch", "true")
    return {"kill_switch": True}


@app.delete("/control/kill-switch")
async def clear_kill_switch():
    r.delete("prometheus_kill_switch")
    return {"kill_switch": False}


@app.get("/artifacts")
async def list_artifacts():
    if not PRODUCTION_DIR.exists():
        return []
    artifacts = []
    for path in sorted(PRODUCTION_DIR.iterdir()):
        if path.is_file():
            artifacts.append({"name": path.name, "size": path.stat().st_size})
    return artifacts
