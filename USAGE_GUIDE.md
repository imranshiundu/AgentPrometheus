# Usage Guide: Commanding the Titan 🔱

Welcome to the bridge of Agent Prometheus. This guide will help you understand how to interact with your multi-agent workforce via Telegram.

---

## 🚦 The Task Lifecycle

Every task you send to Prometheus follows a strict **Execution Lifecycle**. This prevents the AI from "going off the rails" and burning your API budget without oversight.

### 1. Initiation
Send a text message or a voice note to your Telegram bot.
- **Example:** "Research the 3 best Python libraries for vector databases and write a comparison script."

### 2. Spec Review (The Gate)
The **Architect Agent** will generate a `SPEC.md` and send it to you with two interactive buttons: `[ ✅ Approve ]` and `[ ❌ Reject ]`.
- **Review carefully:** This is where you catch potential hallucinations before they cost money.

### 3. Execution (The Forge)
Once approved, **Hephaestus** (the Lead Developer) and **Hermes** (the Scout) start working inside isolated Docker containers. You will receive **Milestone Notifications** as they hit key goals.

### 4. Delivery
Once the task is complete, the bot will send the final results (Python scripts, CSVs, PDF summaries) directly to your Telegram chat.

---

## 💡 Example Task Gallery

Copy and paste these into your bot to see the Titan's full range.

### 🕵️‍♂️ The Researcher (Hermes)
> "Find the 3 most popular React state management libraries in 2024. Extract their pros/cons into a Markdown table and save it as `react_report.md`."

### 🛠 The Specialist (Hephaestus)
> "Build a Python CLI tool that takes a YouTube URL, downloads the audio, and saves it as an MP3. Ensure it uses `yt-dlp` and `ffmpeg`."

### 🏛 The Architect
> "Scaffold a modern Next.js 14 project structure with TailwindCSS, Lucide-React icons, and a basic Login Page UI. Put it in a folder called `next_dashboard`."

### 📡 The Intelligence Officer
> "Monitor Hacker News for any mentions of 'Quantum Computing' today. Give me a summary of the top 3 posts and send me the direct links."

---

## 🛑 Safety & Control

- **The Kill Switch:** If you see the bot looping or making a mistake, send **/stop**. This instantly terminates all agent loops and stops the Docker containers.
- **Whitelist Lock:** The bot only obeys the `TELEGRAM_CHAT_ID` set in the `.env` file. Any other user trying to talk to it will be rejected automatically.

---

## 📂 Finding Your Files
All generated code, research, and artifacts are stored locally on your server in the `workspace/` directory.
- `workspace/research/`: Raw data gathered from the web.
- `workspace/production/`: Final, tested code and scripts.
- `workspace/hive_mind_db/`: The persistent memory node (ChromaDB).

---
**Agent Prometheus: Forged to build. Ready for your command.**
