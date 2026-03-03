import os
import time
import math
import asyncio
import threading
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID, PORT
import database as db
from web import start_web

# ---------------- BOT SETUP ----------------

bot = Client(
    "rename-render-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

# ---------------- HELPER: PROGRESS ----------------
async def progress(current, total, message, start_time, action="Processing"):
    now = time.time()
    diff = now - start_time
    if diff == 0:
        return
    percentage = current * 100 / total
    speed = current / diff
    eta = round((total - current) / speed) if speed > 0 else 0

    # Progress bar using ⬢ for done and ⬡ for remaining
    bar_length = 20
    filled_length = int(bar_length * current // total)
    bar = "⬢" * filled_length + "⬡" * (bar_length - filled_length)

    bar_text = f"""
<b>{action}</b>
{bar} {percentage:.2f}%
<b>🔗 Size :</b> {current / 1024 / 1024:.2f}MB | {total / 1024 / 1024:.2f}MB
<b>🚀 Speed :</b> {speed / 1024 / 1024:.2f}MB/s
<b>⏰ ETA :</b> {eta}s
"""
    try:
        await message.edit(bar_text)
    except:
        pass

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
        [
            InlineKeyboardButton("📢 Updates", url="https://t.me/Anime_UpdatesAU"),
            InlineKeyboardButton("💬 Support", url="https://t.me/AU_Bot_Discussion")
        ],
        [
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
            InlineKeyboardButton("🛠 Help", callback_data="help")
        ]
    ])

    await message.reply_photo(
        photo="https://graph.org/file/0e77ba48a8b7a3b09296f-362372bee0d84fd217.jpg",
        caption=welcome_text,
        reply_markup=buttons
    )

# ---------------- CALLBACKS ----------------

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
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Home", callback_data="start")]
            ])
        )
    elif data == "about":
        await query.message.edit_text(
            text=f"🤖 Bot: 2GB Rename Bot\n👨‍💻 Developer: @{OWNER_ID}\n📌 Purpose: Rename and process files up to 2GB",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Home", callback_data="start")]
            ])
        )

# ---------------- CAPTION ----------------

@bot.on_message(filters.command("setcaption") & filters.private)
async def set_caption_cmd(client, message):
    text = " ".join(message.text.split()[1:])
    db.set_caption(message.from_user.id, text)
    await message.reply("✅ Caption saved")

@bot.on_message(filters.command("seecaption") & filters.private)
async def see_caption_cmd(client, message):
    caption = db.get_caption(message.from_user.id)
    await message.reply(f"📄 Caption: {caption or 'Not set'}")

@bot.on_message(filters.command("removecaption") & filters.private)
async def remove_caption_cmd(client, message):
    db.set_caption(message.from_user.id, None)
    await message.reply("✅ Caption removed")

# ---------------- THUMBNAIL ----------------

@bot.on_message(filters.command("setthumbnail") & filters.private)
async def set_thumb_cmd(client, message):
    if message.reply_to_message and message.reply_to_message.photo:
        path = f"thumbnails/{message.from_user.id}.jpg"
        await message.reply_to_message.download(path)
        db.set_thumb(message.from_user.id, path)
        await message.reply("✅ Thumbnail saved")
    else:
        await message.reply("Reply to a photo to set as thumbnail")

@bot.on_message(filters.command("viewthumbnail") & filters.private)
async def view_thumb_cmd(client, message):
    thumb = db.get_thumb(message.from_user.id)
    if thumb:
        await message.reply_photo(thumb)
    else:
        await message.reply("No thumbnail set")

@bot.on_message(filters.command("removethumbnail") & filters.private)
async def remove_thumb_cmd(client, message):
    db.set_thumb(message.from_user.id, None)
    await message.reply("✅ Thumbnail removed")

# ---------------- METADATA ----------------

@bot.on_message(filters.command("setmetadata") & filters.private)
async def set_metadata_cmd(client, message):
    uid = message.from_user.id
    meta_lines = message.text.split("\n")[1:]
    meta_dict = {}
    for line in meta_lines:
        if "=" in line:
            k, v = line.split("=", 1)
            meta_dict[k.strip()] = v.strip()
    db.set_metadata(uid, str(meta_dict))
    await message.reply("✅ Metadata saved")

@bot.on_message(filters.command("meta") & filters.private)
async def meta_toggle_cmd(client, message):
    uid = message.from_user.id
    arg = message.text.split()[1].lower() if len(message.text.split()) > 1 else None
    if arg == "on":
        db.set_metadata(uid, db.get_metadata(uid) or "{}")
        await message.reply("🟢 Metadata enabled")
    elif arg == "off":
        db.set_metadata(uid, "{}")
        await message.reply("🔴 Metadata disabled")
    else:
        await message.reply("Usage: /meta on or /meta off")

# ---------------- MEDIA ----------------

@bot.on_message(filters.command("setmedia") & filters.private)
async def set_media_cmd(client, message):
    if len(message.text.split()) < 2:
        return await message.reply("Usage: /setmedia video|document|audio")
    mode = message.text.split()[1].lower()
    if mode not in ["video", "document", "audio"]:
        return await message.reply("Choose: video / document / audio")
    db.set_media(message.from_user.id, mode)
    await message.reply(f"✅ Media set to {mode}")

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
        cmd = ["ffmpeg", "-y", "-i", file_path]
        import ast
        meta_dict = ast.literal_eval(metadata)
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

    if mode == "video":
        await client.send_video(
            message.chat.id,
            file_path,
            caption=db.get_caption(uid),
            thumb=thumb,
            progress=progress,
            progress_args=(status, start_time, "📤 Uploading...")
        )
    elif mode == "audio":
        await client.send_audio(
            message.chat.id,
            file_path,
            caption=db.get_caption(uid),
            thumb=thumb,
            progress=progress,
            progress_args=(status, start_time, "📤 Uploading...")
        )
    else:
        await client.send_document(
            message.chat.id,
            file_path,
            caption=db.get_caption(uid),
            thumb=thumb,
            progress=progress,
            progress_args=(status, start_time, "📤 Uploading...")
        )

    os.remove(file_path)
    await status.delete()

# ---------------- RUN ----------------

if __name__ == "__main__":
    # Start web server for Render
    threading.Thread(target=lambda: asyncio.run(start_web())).start()
    # Start Pyrogram bot
    bot.run()
