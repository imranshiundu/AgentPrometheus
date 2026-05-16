import os
import json
import logging
import redis
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME", os.getenv("RUNTIME_APP_NAME", "Workspace Runtime"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
AUTHORIZED_USER_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def check_auth(update: Update):
    """Safety guardrail: only allow the configured owner."""
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logging.warning(f"Unauthorized access attempt by {update.effective_user.id}")
        await update.message.reply_text("⛔ Unauthorized. This runtime only accepts the configured owner.")
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initialize the connection."""
    if not await check_auth(update): return
    await update.message.reply_text(f"🔱 {APP_NAME} online. Send me a task to begin.\n\nUse /connect <PIN> only when pairing the optional local context node.")

async def connect_vision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pair a local context node using a 6-digit PIN."""
    if not await check_auth(update): return
    
    if not context.args:
        await update.message.reply_text("❌ Please provide a PIN. Example: /connect 834912")
        return

    pin = context.args[0]
    
    r.set(f"prometheus_auth_pin:{pin}", "authorized", ex=3600)
    
    try:
        os.makedirs("workspace", exist_ok=True)
        with open("workspace/active_vision_pin.txt", "w") as f:
            f.write(pin)
    except Exception as e:
        logging.error(f"Failed to write PIN file: {e}")

    vps_ip = os.getenv("VPS_PUBLIC_IP", "YOUR_VPS_IP")
    
    install_msg = (
        f"🔐 **PIN {pin} Authorized.**\n\n"
        f"Pairing helper:\n\n"
        f"**Mac/Linux:**\n`curl -sL http://{vps_ip}:8000/vision_node.py | python3`\n\n"
        f"**Windows (PowerShell):**\n`iwr -useb http://{vps_ip}:8000/vision_node.py | iex`"
    )
    
    await update.message.reply_text(install_msg, parse_mode='Markdown')

async def handle_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inbound: receive task and push to the runtime queue."""
    if not await check_auth(update): return
    
    task_text = update.message.text
    task_payload = {
        "chat_id": update.effective_chat.id,
        "task": task_text,
        "status": "queued",
        "source": "telegram"
    }
    r.lpush("prometheus_tasks", json.dumps(task_payload))
    
    await update.message.reply_text("⚙️ Task queued. The runtime will scan evidence and report back.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle approval/rejection gates."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "approve":
        r.set("prometheus_approval", "approved")
        await query.edit_message_text(text="✅ Approved.")
    else:
        r.set("prometheus_approval", "rejected")
        await query.edit_message_text(text="❌ Rejected.")

async def stop_execution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Emergency kill switch: signal runtime pause."""
    if not await check_auth(update): return
    
    r.set("prometheus_kill_switch", "true")
    await update.message.reply_text("🛑 Kill switch signal sent. Runtime loop will pause safely.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Voice-to-text task intake."""
    if not await check_auth(update): return
    
    voice_file = await context.bot.get_file(update.message.voice.file_id)
    file_path = "workspace/voice_task.ogg"
    await voice_file.download_to_drive(file_path)
    
    await update.message.reply_text("🎤 Voice note received. Transcribing...")
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("REAL_API_KEY"))
        audio_file = open(file_path, "rb")
        transcription = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        task_text = transcription.text
        await update.message.reply_text(f"📝 Transcribed Task: \"{task_text}\"\n\nQueued.")
        task_payload = {"chat_id": update.effective_chat.id, "task": task_text, "status": "queued", "source": "telegram_voice"}
        r.lpush("prometheus_tasks", json.dumps(task_payload))
    except Exception as e:
        await update.message.reply_text(f"❌ Transcription failed: {e}")

async def poll_outbound(context: ContextTypes.DEFAULT_TYPE):
    """Outbound: poll Redis for runtime notifications and file deliveries."""
    message = r.rpop("prometheus_notifications")
    if message:
        payload = json.loads(message)
        chat_id = payload.get("chat_id", AUTHORIZED_USER_ID)
        text = payload.get("text")
        is_approval_gate = payload.get("approval_gate", False)
        file_path = payload.get("file_path")
        
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
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('connect', connect_vision))
    application.add_handler(CommandHandler('stop', stop_execution))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_task))
    application.add_handler(CallbackQueryHandler(button_callback))
    job_queue = application.job_queue
    job_queue.run_repeating(poll_outbound, interval=2, first=1)
    print(f"Telegram Gateway for {APP_NAME} is running...")
    application.run_polling()