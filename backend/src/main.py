import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import redis
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from runtime_features import FEATURE_MODES, clear_feature_request, feature_active, list_features, request_feature, set_feature_mode

APP_NAME = os.getenv("APP_NAME", os.getenv("RUNTIME_APP_NAME", "Workspace Runtime"))
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
TASK_QUEUE = os.getenv("PROMETHEUS_TASK_QUEUE", "prometheus_tasks")
LOG_STREAM = os.getenv("PROMETHEUS_LOG_STREAM", "prometheus_logs")
NOTIFICATION_CHANNEL = os.getenv("PROMETHEUS_NOTIFICATION_CHANNEL", "prometheus_notifications")
KILL_SWITCH_KEY = os.getenv("PROMETHEUS_KILL_SWITCH_KEY", "prometheus_kill_switch")
APPROVAL_INDEX = os.getenv("PROMETHEUS_APPROVAL_INDEX", "prometheus_approvals")
APPROVAL_KEY_PREFIX = os.getenv("PROMETHEUS_APPROVAL_KEY_PREFIX", "prometheus_approval")
CONSULTANT_MODEL = os.getenv("PROMETHEUS_CONSULTANT_MODEL", "consultant-model")
CHEAP_MODEL = os.getenv("PROMETHEUS_CHEAP_MODEL", "utility-model")
AUTO_APPLY = os.getenv("PROMETHEUS_AUTO_APPLY", "false").lower() == "true"
WORKSPACE = Path(os.getenv("PROMETHEUS_WORKSPACE", "workspace"))
PRODUCTION_DIR = WORKSPACE / "production"
TOOL_REGISTRY = Path(os.getenv("PROMETHEUS_TOOL_REGISTRY", "config/tool_registry.json"))
TOOL_QUEUE_PREFIX = os.getenv("PROMETHEUS_TOOL_QUEUE_PREFIX", "prometheus_tool")
TOOL_RESULT_PREFIX = os.getenv("PROMETHEUS_TOOL_RESULT_PREFIX", "prometheus_tool_result")
AUTOGPT_TASK_QUEUE = os.getenv("PROMETHEUS_AUTOGPT_TASK_QUEUE", f"{TOOL_QUEUE_PREFIX}:autogpt:tasks")
AUTOGPT_RESULT_PREFIX = os.getenv("PROMETHEUS_AUTOGPT_RESULT_PREFIX", f"{TOOL_RESULT_PREFIX}:autogpt")

app = FastAPI(title=f"{APP_NAME} Runtime API")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True, socket_connect_timeout=3, socket_timeout=3)


class TaskRequest(BaseModel):
    task: str
    chat_id: int | None = None


class FeatureModeRequest(BaseModel):
    mode: str


class FeatureRequest(BaseModel):
    reason: str = "requested by user"


class ToolTaskRequest(BaseModel):
    task: str
    source: str = "dashboard"
    metadata: dict[str, Any] = {}


def utc_now() -> str:
    return datetime.utcnow().isoformat() + "Z"


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


def redis_get(key: str, default: str | None = None) -> str | None:
    try:
        value = r.get(key)
        return value if value is not None else default
    except redis.RedisError:
        return default


def redis_set_json(key: str, value: Any) -> None:
    try:
        r.set(key, json.dumps(value))
    except redis.RedisError as exc:
        raise HTTPException(status_code=503, detail=f"Redis unavailable: {exc}") from exc


def redis_llen(key: str) -> int:
    try:
        return r.llen(key)
    except redis.RedisError:
        return 0


def redis_lrange(key: str, start: int, end: int) -> list[str]:
    try:
        return r.lrange(key, start, end)
    except redis.RedisError:
        return []


def redis_lpush(key: str, value: str) -> int:
    try:
        return r.lpush(key, value)
    except redis.RedisError as exc:
        raise HTTPException(status_code=503, detail=f"Redis unavailable: {exc}") from exc


def approval_key(approval_id: str) -> str:
    return f"{APPROVAL_KEY_PREFIX}:{approval_id}"


def tool_result_key(tool_name: str, run_id: str) -> str:
    if tool_name == "autogpt":
        return f"{AUTOGPT_RESULT_PREFIX}:{run_id}"
    return f"{TOOL_RESULT_PREFIX}:{tool_name}:{run_id}"


def load_tool_registry() -> dict[str, Any]:
    if not TOOL_REGISTRY.exists():
        return {"tools": []}
    data = parse_json(TOOL_REGISTRY.read_text(encoding="utf-8", errors="ignore"), {"tools": []})
    return data if isinstance(data, dict) else {"tools": []}


def tool_by_name(tool_name: str) -> dict[str, Any]:
    for tool in load_tool_registry().get("tools", []):
        if isinstance(tool, dict) and tool.get("name") == tool_name:
            return tool
    raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")


def tool_status(tool: dict[str, Any]) -> dict[str, Any]:
    name = str(tool.get("name"))
    feature_name = str(tool.get("feature_flag") or name)
    queue_name = str(tool.get("queue") or (AUTOGPT_TASK_QUEUE if name == "autogpt" else f"{TOOL_QUEUE_PREFIX}:{name}:tasks"))
    active = feature_active(r, feature_name)
    return {
        **tool,
        "feature_active": active,
        "queue": queue_name,
        "queue_depth": redis_llen(queue_name),
        "connected": active,
        "status": "ready" if active else "feature_inactive",
    }


def read_approval(approval_id: str) -> dict[str, Any]:
    raw = redis_get(approval_key(approval_id))
    if not raw:
        raise HTTPException(status_code=404, detail="Approval not found")
    data = parse_json(raw, None)
    if not isinstance(data, dict):
        raise HTTPException(status_code=500, detail="Approval record is corrupt")
    return data


def update_approval_status(approval_id: str, status: str) -> dict[str, Any]:
    approval = read_approval(approval_id)
    if approval.get("status") not in {"pending", "approved", "rejected"}:
        raise HTTPException(status_code=409, detail=f"Approval is already {approval.get('status')}")
    approval["status"] = status
    approval["updated_at"] = utc_now()
    redis_set_json(approval_key(approval_id), approval)
    return approval


def safe_artifact_path(name: str) -> Path:
    target = (PRODUCTION_DIR / name).resolve()
    root = PRODUCTION_DIR.resolve()
    if target != root and root not in target.parents:
        raise HTTPException(status_code=400, detail="Invalid artifact path")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")
    return target


def list_files(root: Path) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        stat = path.stat()
        files.append({"name": rel, "size": stat.st_size, "modified": int(stat.st_mtime)})
    return files


def feature_or_404(name: str, func):
    try:
        return func()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown feature: {name}") from exc


@app.get("/health")
async def health():
    return {"status": "ok", "redis": redis_health(), "app_name": APP_NAME}


@app.get("/runtime/config")
async def runtime_config():
    return {"app_name": APP_NAME, "runtime": "consultant", "consultant_model": CONSULTANT_MODEL, "cheap_model": CHEAP_MODEL, "auto_apply": AUTO_APPLY, "workspace": str(WORKSPACE), "task_queue": TASK_QUEUE, "log_stream": LOG_STREAM, "notification_channel": NOTIFICATION_CHANNEL, "approval_index": APPROVAL_INDEX, "feature_modes": sorted(FEATURE_MODES), "tool_registry": str(TOOL_REGISTRY)}


@app.get("/runtime/routes")
async def runtime_routes():
    routes = []
    for route in app.routes:
        methods = sorted(getattr(route, "methods", []) or [])
        path = getattr(route, "path", "")
        if path:
            routes.append({"path": path, "methods": methods})
    return routes


@app.get("/features")
async def get_features():
    return list_features(r)


@app.put("/features/{feature_name}")
async def update_feature(feature_name: str, request: FeatureModeRequest):
    if request.mode not in FEATURE_MODES:
        raise HTTPException(status_code=400, detail="Feature mode must be one of: off, auto, on")
    return feature_or_404(feature_name, lambda: set_feature_mode(r, feature_name, request.mode))


@app.post("/features/{feature_name}/request")
async def request_runtime_feature(feature_name: str, request: FeatureRequest):
    return feature_or_404(feature_name, lambda: request_feature(r, feature_name, request.reason))


@app.delete("/features/{feature_name}/request")
async def clear_runtime_feature_request(feature_name: str):
    return feature_or_404(feature_name, lambda: clear_feature_request(r, feature_name))


@app.get("/tools")
async def get_tools():
    return [tool_status(tool) for tool in load_tool_registry().get("tools", []) if isinstance(tool, dict)]


@app.get("/tools/{tool_name}")
async def get_tool(tool_name: str):
    return tool_status(tool_by_name(tool_name))


@app.post("/tools/{tool_name}/tasks")
async def create_tool_task(tool_name: str, request: ToolTaskRequest):
    tool = tool_status(tool_by_name(tool_name))
    feature_name = str(tool.get("feature_flag") or tool_name)
    if not feature_active(r, feature_name):
        raise HTTPException(status_code=409, detail=f"Tool feature is not active: {feature_name}")
    task = request.task.strip()
    if not task:
        raise HTTPException(status_code=400, detail="Task cannot be empty")
    run_id = uuid.uuid4().hex[:12]
    payload = {"run_id": run_id, "tool": tool_name, "task": task, "source": request.source, "status": "queued", "metadata": request.metadata, "created_at": utc_now()}
    redis_lpush(str(tool["queue"]), json.dumps(payload))
    redis_set_json(tool_result_key(tool_name, run_id), payload)
    return {**payload, "queue": tool["queue"]}


@app.get("/tools/{tool_name}/results/{run_id}")
async def get_tool_result(tool_name: str, run_id: str):
    tool_by_name(tool_name)
    raw = redis_get(tool_result_key(tool_name, run_id))
    if not raw:
        raise HTTPException(status_code=404, detail="Tool result not found")
    parsed = parse_json(raw, None)
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=500, detail="Tool result is corrupt")
    return parsed


@app.get("/vision_node.py")
async def get_vision_node():
    path = Path("vision_node.py")
    if not path.exists():
        raise HTTPException(status_code=404, detail="vision_node.py is not mounted")
    return FileResponse(path)


@app.get("/stats")
async def get_stats():
    health = redis_health()
    pending = [item for item in await list_approvals() if item.get("status") == "pending"]
    features = list_features(r)
    tools = [tool_status(tool) for tool in load_tool_registry().get("tools", []) if isinstance(tool, dict)]
    return {"tokens": redis_get("prometheus_token_count", "0") or "0", "health": health.upper(), "active_agents": redis_get("prometheus_active_count", "1 / 1") or "1 / 1", "queue_depth": redis_llen(TASK_QUEUE), "log_count": redis_llen(LOG_STREAM), "notification_count": redis_llen(NOTIFICATION_CHANNEL), "pending_approval_count": len(pending), "active_feature_count": len([item for item in features if item.get("active")]), "tool_count": len(tools), "connected_tool_count": len([item for item in tools if item.get("connected")]), "kill_switch": redis_get(KILL_SWITCH_KEY) == "true", "runtime": "consultant", "app_name": APP_NAME}


@app.get("/logs")
async def get_logs(limit: int = 100):
    limit = max(1, min(limit, 500))
    logs = redis_lrange(LOG_STREAM, 0, limit - 1)
    return [parse_json(item, {"msg": item}) for item in logs]


@app.get("/queue")
async def get_queue(limit: int = 50):
    limit = max(1, min(limit, 200))
    tasks = redis_lrange(TASK_QUEUE, 0, limit - 1)
    return [parse_json(item, {"task": item}) for item in tasks]


@app.get("/notifications")
async def get_notifications(limit: int = 50):
    limit = max(1, min(limit, 200))
    notifications = redis_lrange(NOTIFICATION_CHANNEL, 0, limit - 1)
    return [parse_json(item, {"text": item}) for item in notifications]


@app.get("/approvals")
async def list_approvals(limit: int = 50):
    limit = max(1, min(limit, 100))
    ids = redis_lrange(APPROVAL_INDEX, 0, limit - 1)
    approvals: list[dict[str, Any]] = []
    for approval_id in ids:
        raw = redis_get(approval_key(approval_id))
        parsed = parse_json(raw, None)
        if isinstance(parsed, dict):
            approvals.append(parsed)
    return approvals


@app.post("/approvals/{approval_id}/approve")
async def approve(approval_id: str):
    return update_approval_status(approval_id, "approved")


@app.post("/approvals/{approval_id}/reject")
async def reject(approval_id: str):
    return update_approval_status(approval_id, "rejected")


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            logs = redis_lrange(LOG_STREAM, 0, 49)
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
    redis_lpush(TASK_QUEUE, json.dumps(payload))
    return {"queued": True, "queue_depth": redis_llen(TASK_QUEUE)}


@app.post("/control/kill-switch")
async def trigger_kill_switch():
    try:
        r.set(KILL_SWITCH_KEY, "true")
    except redis.RedisError as exc:
        raise HTTPException(status_code=503, detail=f"Redis unavailable: {exc}") from exc
    return {"kill_switch": True}


@app.delete("/control/kill-switch")
async def clear_kill_switch():
    try:
        r.delete(KILL_SWITCH_KEY)
    except redis.RedisError as exc:
        raise HTTPException(status_code=503, detail=f"Redis unavailable: {exc}") from exc
    return {"kill_switch": False}


@app.get("/artifacts")
async def list_artifacts():
    return list_files(PRODUCTION_DIR)


@app.get("/artifacts/{artifact_path:path}")
async def download_artifact(artifact_path: str):
    return FileResponse(safe_artifact_path(artifact_path))


@app.get("/reports")
async def list_reports():
    files = list_files(PRODUCTION_DIR)
    return [item for item in files if item["name"].endswith((".json", ".md", ".txt"))]
