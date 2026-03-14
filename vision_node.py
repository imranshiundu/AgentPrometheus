import asyncio
import websockets
import pyautogui
import mss
import base64
import json
import random
import time

# 🚨 THE KILL SWITCH: Slam mouse to any screen corner to terminate the AI.
pyautogui.FAILSAFE = True

# REPLACE THIS with the IP address of your remote VPS
VPS_WEBSOCKET_URL = "ws://YOUR_VPS_IP:8765"

async def capture_and_stream(websocket, pin):
    """Takes a screenshot every 3 seconds and streams it to the VPS."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Primary monitor
        
        while True:
            # Capture screen
            sct_img = sct.grab(monitor)
            
            # Convert to raw bytes, then Base64 so it can travel over WebSockets
            img_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)
            encoded_img = base64.b64encode(img_bytes).decode('utf-8')
            
            payload = {
                "type": "vision_stream",
                "pin": pin,
                "image_b64": encoded_img,
                "screen_width": monitor["width"],
                "screen_height": monitor["height"]
            }
            
            try:
                await websocket.send(json.dumps(payload))
                await asyncio.sleep(3) # Throttle to prevent network flooding
            except websockets.ConnectionClosed:
                print("Connection to VPS lost. Stopping vision stream.")
                break

async def listen_for_actions(websocket, pin):
    """Listens for AI commands from the VPS and executes them on your laptop."""
    async for message in websocket:
        try:
            command = json.loads(message)
            
            # Security Check: Only accept commands matching our session PIN
            if command.get("pin") != pin:
                continue

            action = command.get("action")
            
            if action == "click":
                x, y = command.get("x"), command.get("y")
                print(f"🤖 AI clicked at X:{x}, Y:{y}")
                pyautogui.click(x=x, y=y)
                
            elif action == "type":
                text = command.get("text")
                print(f"🤖 AI typed: {text}")
                pyautogui.write(text, interval=0.05)
                
            elif action == "press":
                key = command.get("key")
                print(f"🤖 AI pressed: {key}")
                pyautogui.press(key)
                
        except Exception as e:
            print(f"Error executing AI command: {e}")

async def main():
    # 1. Generate the pairing PIN
    session_pin = str(random.randint(100000, 999999))
    print("========================================")
    print("🔱 PROMETHEUS VISION NODE INITIALIZED")
    print(f"🔐 Your Pairing PIN is: {session_pin}")
    print("📲 Send '/connect " + session_pin + "' to your Telegram Bot.")
    print("🚨 REMEMBER: Slam mouse to any screen corner to emergency abort.")
    print("========================================")

    # 2. Connect to the VPS
    try:
        async with websockets.connect(VPS_WEBSOCKET_URL) as websocket:
            print("✅ Connected to Remote Prometheus Hive Mind.")
            
            # 3. Run the eyes (camera) and hands (listener) simultaneously
            await asyncio.gather(
                capture_and_stream(websocket, session_pin),
                listen_for_actions(websocket, session_pin)
            )
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
