import os
import json
import logging
from datetime import datetime
import redis
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv

from runtime_features import clear_feature_request, feature_active, list_features, set_feature_mode

load_dotenv()

APP_NAME = os.getenv("APP_NAME", os.getenv("RUNTIME_APP_NAME", "Workspace Runtime"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
AUTHORIZED_USER_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
APPROVAL_KEY_PREFIX = os.getenv("PROMETHEUS_APPROVAL_KEY_PREFIX", "prometheus_approval")

r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


def approval_key(approval_id: str) -> str:
    return f"{APPROVAL_KEY_PREFIX}:{approval_id}"


def update_approval_status(approval_id: str, status: str) -> bool:
    raw = r.get(approval_key(approval_id))
    if not raw:
        return False
    approval = json.loads(raw)
    approval["status"] = status
    approval["updated_at"] = datetime.utcnow().isoformat() + "Z"
    r.set(approval_key(approval_id), json.dumps(approval))
    return True


def feature_text() -> str:
    rows = []
    for feature in list_features(r):
        marker = "🟢" if feature.get("active") else "⚪"
        rows.append(f"{marker} {feature['name']} — {feature['mode']} — {feature['ram']}")
    return "\n".join(rows)


def feature_keyboard() -> InlineKeyboardMarkup:
    keyboard = []
    for feature in list_features(r):
        name = feature["name"]
        keyboard.append([
            InlineKeyboardButton(f"{name}: OFF", callback_data=f"feature:{name}:off"),
            InlineKeyboardButton("AUTO", callback_data=f"feature:{name}:auto"),
            InlineKeyboardButton("ON", callback_data=f"feature:{name}:on"),
        ])
        if feature.get("requested"):
            keyboard.append([InlineKeyboardButton(f"clear {name} auto request", callback_data=f"feature_clear:{name}")])
    return InlineKeyboardMarkup(keyboard)


async def check_auth(update: Update):
    """Safety guardrail: only allow the configured owner."""
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logging.warning(f"Unauthorized access attempt by {update.effective_user.id}")
        if update.message:
            await update.message.reply_text("⛔ Unauthorized. This runtime only accepts the configured owner.")
        elif update.callback_query:
            await update.callback_query.answer("Unauthorized", show_alert=True)
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initialize the connection."""
    if not await check_auth(update): return
    await update.message.reply_text(
        f"🔱 {APP_NAME} online. Send me a task to begin.\n\n"
        "Commands:\n"
        "/features — heavy feature controls\n"
        "/telegram_off — disable Telegram task intake behavior\n"
        "/telegram_auto — let runtime request Telegram only when needed\n"
        "/telegram_on — keep Telegram behavior enabled\n"
        "/connect <PIN> — pair optional local context node"
    )

async def show_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    await update.message.reply_text("Heavy feature modes:\n\n" + feature_text(), reply_markup=feature_keyboard())

async def telegram_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    set_feature_mode(r, "telegram", "off")
    await update.message.reply_text("Telegram feature mode set to OFF. This running bot can still receive this command until the container is stopped, but task intake/notifications should be considered disabled.")

async def telegram_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    set_feature_mode(r, "telegram", "auto")
    await update.message.reply_text("Telegram feature mode set to AUTO.")

async def telegram_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    set_feature_mode(r, "telegram", "on")
    await update.message.reply_text("Telegram feature mode set to ON.")

async def connect_vision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pair a local context node using a 6-digit PIN."""
    if not await check_auth(update): return
    if not feature_active(r, "vision"):
        await update.message.reply_text("Vision bridge is not active. Set vision to AUTO/ON from /features first.")
        return
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
    if not feature_active(r, "telegram"):
        await update.message.reply_text("Telegram task intake is disabled. Use /telegram_on or /features to enable it.")
        return
    task_payload = {"chat_id": update.effective_chat.id, "task": update.message.text, "status": "queued", "source": "telegram"}
    r.lpush("prometheus_tasks", json.dumps(task_payload))
    await update.message.reply_text("⚙️ Task queued. The runtime will scan evidence and report back.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle approval/rejection gates and feature buttons."""
    query = update.callback_query
    await query.answer()
    if not await check_auth(update): return
    data = query.data or ""
    if data.startswith("feature:"):
        _, name, mode = data.split(":", 2)
        try:
            feature = set_feature_mode(r, name, mode)
            await query.edit_message_text(text=f"Feature updated: {feature['name']} → {feature['mode']}\n\n" + feature_text(), reply_markup=feature_keyboard())
        except KeyError:
            await query.edit_message_text(text="Unknown feature.")
        return
    if data.startswith("feature_clear:"):
        _, name = data.split(":", 1)
        try:
            clear_feature_request(r, name)
            await query.edit_message_text(text=f"Cleared auto request for {name}.\n\n" + feature_text(), reply_markup=feature_keyboard())
        except KeyError:
            await query.edit_message_text(text="Unknown feature.")
        return
    decision, _, approval_id = data.partition(":")
    status = "approved" if decision == "approve" else "rejected"
    if approval_id:
        updated = update_approval_status(approval_id, status)
        await query.edit_message_text(text=("✅ Approved." if status == "approved" else "❌ Rejected.") if updated else "⚠️ Approval request not found or expired.")
    else:
        r.set("prometheus_approval", status)
        await query.edit_message_text(text="✅ Approved." if status == "approved" else "❌ Rejected.")

async def stop_execution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Emergency kill switch: signal runtime pause."""
    if not await check_auth(update): return
    r.set("prometheus_kill_switch", "true")
    await update.message.reply_text("🛑 Kill switch signal sent. Runtime loop will pause safely.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Voice-to-text task intake."""
    if not await check_auth(update): return
    if not feature_active(r, "voice"):
        await update.message.reply_text("Voice transcription is disabled. Enable voice from /features first.")
        return
    voice_file = await context.bot.get_file(update.message.voice.file_id)
    file_path = "workspace/voice_task.ogg"
    await voice_file.download_to_drive(file_path)
    await update.message.reply_text("🎤 Voice note received. Transcribing...")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("REAL_API_KEY") or os.getenv("OPENAI_API_KEY"))
        with open(file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        task_text = transcription.text
        await update.message.reply_text(f"📝 Transcribed Task: \"{task_text}\"\n\nQueued.")
        r.lpush("prometheus_tasks", json.dumps({"chat_id": update.effective_chat.id, "task": task_text, "status": "queued", "source": "telegram_voice"}))
    except Exception as e:
        await update.message.reply_text(f"❌ Transcription failed: {e}")

async def poll_outbound(context: ContextTypes.DEFAULT_TYPE):
    """Outbound: poll Redis for runtime notifications and file deliveries."""
    if not feature_active(r, "telegram"):
        return
    message = r.rpop("prometheus_notifications")
    if message:
        payload = json.loads(message)
        chat_id = payload.get("chat_id", AUTHORIZED_USER_ID)
        text = payload.get("text")
        is_approval_gate = payload.get("approval_gate", False)
        approval_id = payload.get("approval_id")
        file_path = payload.get("file_path")
        if file_path and os.path.exists(file_path):
            await context.bot.send_document(chat_id=chat_id, document=open(file_path, 'rb'), caption=text)
        elif is_approval_gate:
            suffix = f":{approval_id}" if approval_id else ""
            keyboard = [[InlineKeyboardButton("✅ Approve", callback_data=f"approve{suffix}")], [InlineKeyboardButton("❌ Reject", callback_data=f"reject{suffix}")]]
            await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')

if __name__ == '__main__':
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN not found in environment.")
        exit(1)
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('features', show_features))
    application.add_handler(CommandHandler('telegram_off', telegram_off))
    application.add_handler(CommandHandler('telegram_auto', telegram_auto))
    application.add_handler(CommandHandler('telegram_on', telegram_on))
    application.add_handler(CommandHandler('connect', connect_vision))
    application.add_handler(CommandHandler('stop', stop_execution))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_task))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.job_queue.run_repeating(poll_outbound, interval=2, first=1)
    print(f"Telegram Gateway for {APP_NAME} is running...")
    application.run_polling()
