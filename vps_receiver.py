import asyncio
import websockets
import json
import base64
import os
import redis

# --- PROMETHEUS VISUAL CORTEX (VPS RECEIVER) ---
# This script bridges the local laptop's vision node to the cloud AI brain.

WORKSPACE_DIR = "./workspace"
os.makedirs(WORKSPACE_DIR, exist_ok=True)

# The PIN file authorized via Telegram
PIN_FILE = os.path.join(WORKSPACE_DIR, "active_vision_pin.txt")

# Redis for command bridging
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

async def handle_vision_stream(websocket, path):
    """Listens for incoming screenshots from the laptop."""
    print("🌐 Incoming connection request from a Vision Node...")
    
    try:
        async for message in websocket:
            data = json.loads(message)
            incoming_pin = data.get("pin")
            
            # 1. PIN Authorization Check
            try:
                with open(PIN_FILE, "r") as f:
                    authorized_pin = f.read().strip()
            except FileNotFoundError:
                authorized_pin = None

            if not authorized_pin or str(incoming_pin) != str(authorized_pin):
                print(f"❌ Rejecting unauthorized Vision Node (PIN mismatch: {incoming_pin} vs {authorized_pin}).")
                await websocket.close()
                return

            # 2. Process Vision Stream
            if data.get("type") == "vision_stream":
                # Save latest image to workspace for the Orchestrator
                img_data = base64.b64decode(data.get("image_b64"))
                img_path = os.path.join(WORKSPACE_DIR, "latest_screen.png")
                
                with open(img_path, "wb") as f:
                    f.write(img_data)
                
                # Update high-speed Redis state for 'vitals'
                r.set(f"prometheus_eyes:{incoming_pin}", data.get("image_b64"))
                r.set(f"prometheus_screen_res:{incoming_pin}", json.dumps({
                    "width": data.get("screen_width"),
                    "height": data.get("screen_height")
                }))

                # 3. Check for Outbound Commands (Hands)
                command_raw = r.rpop(f"prometheus_hands:{incoming_pin}")
                if command_raw:
                    await websocket.send(command_raw)
                    print(f"🤖 Sent command to node: {command_raw}")

    except websockets.exceptions.ConnectionClosed:
        print("🔌 Vision Node disconnected.")
    except Exception as e:
        print(f"⚠️ Error in Vision loop: {e}")

async def main():
    print("👁️ Prometheus Visual Cortex Online. Listening on port 8765...")
    async with websockets.serve(handle_vision_stream, "0.0.0.0", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
