# Remote Control: Vision Nodes & The Ghost in the Machine 👻

Agent Prometheus can now "break out" of its server and control your physical laptop or remote desktops using **Vision Nodes**.

---

## 👁 How It Works (The Loop)

1.  **The Sight:** Your local computer captures a screenshot and streams it to the VPS via a secure WebSocket.
2.  **The Logic:** The Prometheus Orchestrator (using Claude 3.5 Sonnet Vision) analyzes the image to find UI elements.
3.  **The Action:** The Orchestrator sends mouse/keyboard commands back to your computer to execute.

---

## 🚀 Getting Started

### 1. Locally (Your Laptop)
You need to run the `vision_node.py` locally. This script is lightweight and does not require Docker.

-   **Install Dependencies:**
    ```bash
    pip install pyautogui mss websockets
    ```
-   **Run the Node:**
    ```bash
    python vision_node.py
    ```
    The terminal will show a **Pairing PIN** (e.g., `🔐 PIN: 482910`).

### 2. On Telegram
Send the pairing command to your bot:
```text
/connect 482910
```

### 3. Command the AI
Ask the bot to perform a GUI-based task:
```text
"Open my browser, go to Google, and search for the latest Prometheus V5 release notes."
```

---

## 🚨 THE HARDWARE KILL SWITCH

Because Vision AI can hallucinate coordinates or click the wrong things, we have implemented a **fail-safe**.

> [!CAUTION]
> If the AI starts performing unrequested actions, **slam your mouse pointer into any of the four extreme corners of your screen.** This instantly crashes the local Vision Node and locks the AI out.

---

## 🛡 Security & Reality Check

1.  **Latency:** Vision-based control is slower than code (3-10 seconds per click). It is best used for data entry or scraping sites with no API.
2.  **Locked Screens:** OS security prevents virtual input on locked screens. Your laptop must be awake for the AI to move the mouse.
3.  **Encrypted Tunnel:** All screenshots and commands travel over an encrypted WebSocket tunnel pairing your session PIN to your Telegram ID.

---
**Agent Prometheus is now more than a brain—it has eyes and hands.**
