import os
import json
import logging
import redis
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()

# --- SECURITY CONFIGURATION ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
AUTHORIZED_USER_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))  # Hardcoded User ID Check
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

# Initialize Redis for M2M communication
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def check_auth(update: Update):
    """Safety Guardrail: Only allow the authorized owner."""
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logging.warning(f"Unauthorized access attempt by {update.effective_user.id}")
        await update.message.reply_text("⛔ Unauthorized. This Titan only obeys its creator.")
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initialize the connection."""
    if not await check_auth(update): return
    await update.message.reply_text("🔱 Agent Prometheus Online. Send me a task to begin the forge.\n\nUse /connect <PIN> to pair a local Vision Node.")

async def connect_vision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pair a local Vision Node using a 6-digit PIN."""
    if not await check_auth(update): return
    
    if not context.args:
        await update.message.reply_text("❌ Please provide a PIN. Example: /connect 834912")
        return

    pin = context.args[0]
    # Store authorized PIN in Redis with a 1-hour expiration
    r.set(f"prometheus_auth_pin:{pin}", "authorized", ex=3600)
    
    await update.message.reply_text(f"🔐 PIN {pin} Authorized. Waiting for the local Vision Node to handshake...")

async def handle_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inbound: Receive task and push to the Orchestrator."""
    if not await check_auth(update): return
    
    task_text = update.message.text
    # Push to Redis Queue for the Orchestrator
    task_payload = {
        "chat_id": update.effective_chat.id,
        "task": task_text,
        "status": "pending_spec"
    }
    r.lpush("prometheus_tasks", json.dumps(task_payload))
    
    await update.message.reply_text("⚙️ Task acknowledged. The Architect is drafting the SPEC.md...")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Approval/Rejection gates."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "approve":
        r.set("prometheus_approval", "approved")
        await query.edit_message_text(text="✅ Spec Approved. Hephaestus is starting the coding phase.")
    else:
        r.set("prometheus_approval", "rejected")
        await query.edit_message_text(text="❌ Spec Rejected. Task aborted.")

async def stop_execution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Emergency Kill Switch: Stop all agents and Docker containers."""
    if not await check_auth(update): return
    
    # Send kill signal via Redis
    r.set("prometheus_kill_switch", "true")
    
    # Also attempt a local docker-compose stop
    import subprocess
    try:
        subprocess.run(["docker-compose", "stop"], check=True)
        await update.message.reply_text("🛑 EMERGENCY STOP: All agent loops signaled and Docker containers halted.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Kill switch triggered, but Docker stop failed: {e}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Voice-to-Text Initiation: Transcribe memo via Whisper."""
    if not await check_auth(update): return
    
    voice_file = await context.bot.get_file(update.message.voice.file_id)
    file_path = "workspace/voice_task.ogg"
    await voice_file.download_to_drive(file_path)
    
    await update.message.reply_text("🎤 Voice note received. Transcribing via Whisper...")
    
    # Simple transcription logic (assumes openai client initialized or uses litellm gateway)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("REAL_API_KEY"))
        audio_file = open(file_path, "rb")
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
        task_text = transcription.text
        await update.message.reply_text(f"📝 Transcribed Task: \"{task_text}\"\n\nStarting the forge...")
        
        # Push to Redis Queue
        task_payload = {"chat_id": update.effective_chat.id, "task": task_text, "status": "pending_spec"}
        r.lpush("prometheus_tasks", json.dumps(task_payload))
    except Exception as e:
        await update.message.reply_text(f"❌ Transcription failed: {e}")

async def poll_outbound(context: ContextTypes.DEFAULT_TYPE):
    """Outbound: Poll Redis for agent notifications and file deliveries."""
    message = r.rpop("prometheus_notifications")
    if message:
        payload = json.loads(message)
        chat_id = payload.get("chat_id", AUTHORIZED_USER_ID)
        text = payload.get("text")
        is_approval_gate = payload.get("approval_gate", False)
        file_path = payload.get("file_path") # New: Support for artifact delivery
        
        if file_path and os.path.exists(file_path):
            await context.bot.send_document(chat_id=chat_id, document=open(file_path, 'rb'), caption=text)
        elif is_approval_gate:
            keyboard = [
                [InlineKeyboardButton("✅ Approve", callback_data="approve")],
                [InlineKeyboardButton("❌ Reject", callback_data="reject")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')

if __name__ == '__main__':
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN not found in environment.")
        exit(1)
        
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('connect', connect_vision)) # Vision Node Pairing
    application.add_handler(CommandHandler('stop', stop_execution)) # New Kill Switch
    application.add_handler(MessageHandler(filters.VOICE, handle_voice)) # New Voice Support
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_task))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Periodically check for outbound notifications from agents
    job_queue = application.job_queue
    job_queue.run_repeating(poll_outbound, interval=2, first=1)
    
    print("Telegram Gateway (The Front Desk) is running...")
    application.run_polling()
