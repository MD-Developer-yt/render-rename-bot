import os
import time
import math
import asyncio
import threading
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID
import database as db

# ---------------- BOT SETUP ----------------
bot = Client(
    "rename-render-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

# ---------------- PROGRESS BAR ----------------
PROGRESS_BAR = """\n
<b>🔗 Size :</b> {1} | {2}
<b>⏳ Done :</b> {0}%
<b>🚀 Speed :</b> {3}/s
<b>⏰ ETA :</b> {4}
"""

def format_time(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}h {m}m {s}s" if h else f"{m}m {s}s"

async def progress(current, total, message, start_time, action="Processing"):
    now = time.time()
    diff = now - start_time
    if diff == 0:
        return
    percentage = current * 100 / total
    speed = current / diff
    eta_sec = round((total - current) / speed) if speed > 0 else 0
    bar_count = int(percentage // 4)  # 25 blocks total
    bar = "⬡" * bar_count + "⬢" * (25 - bar_count)
    bar_text = PROGRESS_BAR.format(
        f"{percentage:.2f} {bar}",
        f"{current / 1024 / 1024:.2f}MB",
        f"{total / 1024 / 1024:.2f}MB",
        f"{speed / 1024 / 1024:.2f}MB",
        format_time(eta_sec)
    )
    try:
        await message.edit(bar_text)
    except:
        pass

# ---------------- WEB SERVER ----------------
from fastapi import FastAPI
import uvicorn

app = FastAPI()
PORT = int(os.environ.get("PORT", 8080))

@app.get("/")
async def root():
    return {"status": "Bot is alive"}

def start_web():
    uvicorn.run(app, host="0.0.0.0", port=PORT)

# ---------------- START COMMAND ----------------
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    db.add_user(message.from_user.id)
    welcome_text = (
        f"👋 Hello {message.from_user.first_name}!\n\n"
        "🤖 Welcome to 2GB Rename Bot\n"
        "📂 Send video / document / audio\n\n"
        "Use /help to see all commands."
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Updates", url="https://t.me/Anime_UpdatesAU"),
         InlineKeyboardButton("💬 Support", url="https://t.me/AU_Bot_Discussion")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about"),
         InlineKeyboardButton("🛠 Help", callback_data="help")]
    ])
    await message.reply_photo(
        photo="https://graph.org/file/0e77ba48a8b7a3b09296f-362372bee0d84fd217.jpg",
        caption=welcome_text,
        reply_markup=buttons
    )

# ---------------- CALLBACK HANDLER ----------------
@bot.on_callback_query()
async def cb_handler(client, query):
    data = query.data
    if data == "help":
        await query.message.edit_text(
            text=(
                "/setcaption - Set caption\n"
                "/removecaption - Remove caption\n"
                "/seecaption - View caption\n"
                "/setthumbnail - Set thumbnail\n"
                "/removethumbnail - Remove thumbnail\n"
                "/viewthumbnail - View thumbnail\n"
                "/setmetadata - Set metadata\n"
                "/meta on/off - Toggle metadata\n"
                "/setmedia video|document|audio\n"
            ),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="start")]])
        )
    elif data == "about":
        await query.message.edit_text(
            text=f"🤖 Bot: 2GB Rename Bot\n👨‍💻 Developer: @{OWNER_ID}\n📌 Purpose: Rename and process files up to 2GB",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="start")]])
        )
    elif data == "start":
        await start_cmd(client, query.message)

# ---------------- FILE HANDLER ----------------
@bot.on_message(filters.video | filters.document | filters.audio)
async def handle_file(client, message):
    uid = message.from_user.id
    media = message.video or message.document or message.audio
    if media.file_size > MAX_FILE_SIZE:
        return await message.reply("❌ File exceeds 2GB limit")

    status = await message.reply("📥 Starting download...")
    start_time = time.time()

    file_path = await message.download(
        file_name=f"{uid}_{int(time.time())}",
        progress=progress,
        progress_args=(status, start_time, "📥 Downloading...")
    )

    meta_enabled = db.get_metadata(uid) != "{}"
    metadata = db.get_metadata(uid)

    if metadata and meta_enabled:
        await status.edit("🛠 Applying metadata...")
        output_path = file_path + "_meta.mp4"
        import ast
        meta_dict = ast.literal_eval(metadata)
        cmd = ["ffmpeg", "-y", "-i", file_path]
        for k, v in meta_dict.items():
            cmd.extend(["-metadata", f"{k}={v}"])
        cmd.extend(["-codec", "copy", output_path])
        subprocess.run(cmd)
        os.remove(file_path)
        file_path = output_path

    await status.edit("📤 Uploading...")
    start_time = time.time()
    mode = db.get_media(uid) or "document"
    thumb = db.get_thumb(uid)

    send_kwargs = dict(
        chat_id=message.chat.id,
        caption=db.get_caption(uid),
        thumb=thumb,
        progress=progress,
        progress_args=(status, start_time, "📤 Uploading...")
    )

    if mode == "video":
        await client.send_video(file_path, **send_kwargs)
    elif mode == "audio":
        await client.send_audio(file_path, **send_kwargs)
    else:
        await client.send_document(file_path, **send_kwargs)

    os.remove(file_path)
    await status.delete()

# ---------------- RUN ----------------
if __name__ == "__main__":
    threading.Thread(target=start_web).start()
    bot.run()
