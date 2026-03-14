import os
import redis
import json
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio

app = FastAPI()

# Enable CORS for the Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

@app.get("/vision_node.py")
async def get_vision_node():
    return FileResponse("vision_node.py")

@app.get("/stats")
async def get_stats():
    # Mock stats or pull from Redis keys
    stats = {
        "tokens": r.get("prometheus_token_count") or "42.8k",
        "health": "OPTIMAL",
        "active_agents": r.get("prometheus_active_count") or "3 / 5",
        "efficiency": "92.4%"
    }
    return stats

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    while True:
        # Pull the latest logs from Redis
        log = r.rpop("prometheus_logs")
        if log:
            await websocket.send_text(log)
        await asyncio.sleep(1)

@app.get("/artifacts")
async def list_artifacts():
    workspace_path = "workspace/production"
    if not os.path.exists(workspace_path):
        return []
    return os.listdir(workspace_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
