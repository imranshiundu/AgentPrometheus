import asyncio
import websockets
import json
import redis
import os

# --- VPS VISION SERVER (The Receiver) ---
# This server acts as the bridge between your remote agents and your local Vision Node.

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

# Active connections: pin -> websocket
active_nodes = {}

async def handle_node(websocket, path):
    """Handles incoming WebSocket connections from local Vision Nodes."""
    try:
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")
            pin = str(data.get("pin"))

            if msg_type == "vision_stream":
                # Check if this PIN was authorized via Telegram
                authorized_pin = r.get(f"prometheus_auth_pin:{pin}")
                if not authorized_pin:
                    # Not yet authorized, or wrong PIN
                    continue

                # Store the connection
                active_nodes[pin] = websocket
                
                # Store the latest screenshot in Redis for the Orchestrator to see
                # We use a set/get pattern for the "Eyes"
                r.set(f"prometheus_eyes:{pin}", data.get("image_b64"))
                r.set(f"prometheus_screen_res:{pin}", json.dumps({
                    "width": data.get("screen_width"),
                    "height": data.get("screen_height")
                }))

                # Periodically check Redis for commands to send BACK to the node
                command_raw = r.rpop(f"prometheus_hands:{pin}")
                if command_raw:
                    await websocket.send(command_raw)

    except Exception as e:
        print(f"Vision Node loop error: {e}")
    finally:
        # Cleanup
        for pin, ws in list(active_nodes.items()):
            if ws == websocket:
                del active_nodes[pin]
                break

async def main():
    print("🔱 Prometheus Vision Bridge (The Receiver) is starting on port 8765...")
    async with websockets.serve(handle_node, "0.0.0.0", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
