import os
import time
import asyncio
import threading
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import add_user, set_caption, get_caption, set_thumb, get_thumb, set_media, get_media

# ---------------- CONFIG ---------------- #
API_ID = int(os.environ.get("API_ID", 123456))
API_HASH = os.environ.get("API_HASH", "your_api_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")
FORCE_JOIN = os.environ.get("FORCE_JOIN")  # Telegram channel username
OWNER_ID = int(os.environ.get("OWNER_ID", 123456789))  # Your Telegram ID

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

METADATA_DEFAULT = {
    "title": "@Anime_UpdatesAU",
    "author": "@Anime_UpdatesAU",
    "artist": "@Anime_UpdatesAU",
    "audio": "@Anime_UpdatesAU",
    "video": "@Anime_UpdatesAU",
    "subtitle": "@Anime_UpdatesAU",
    "encoded_by": "@Anime_UpdatesAU"
}

# ---------------- BOT INIT ---------------- #
bot = Client(
    "rename-render-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

os.makedirs("downloads", exist_ok=True)
os.makedirs("thumbnails", exist_ok=True)

USER_METADATA = {}
META_ENABLED = {}

# ---------------- PROGRESS ---------------- #
async def progress(current, total, message, start_time, action="Processing"):
    now = time.time()
    diff = now - start_time
    if diff == 0:
        diff = 1
    percent = current * 100 / total
    speed = current / diff
    eta = int((total - current) / speed)
    bar = "█" * int(percent / 5) + "░" * (20 - int(percent / 5))
    text = f"{action}\n[{bar}] {percent:.2f}%\nSpeed: {speed/1024/1024:.2f} MB/s\nETA: {eta}s"
    try:
        asyncio.create_task(message.edit(text))
    except:
        pass

# ---------------- FORCE JOIN ---------------- #
async def force_join_check(client, message):
    if message.from_user.id == OWNER_ID:
        return True
    if not FORCE_JOIN:
        return True
    try:
        user = await client.get_chat_member(FORCE_JOIN, message.from_user.id)
        if user.status in ["left", "kicked"]:
            await message.reply(f"❌ Join @{FORCE_JOIN} first")
            return False
        return True
    except:
        await message.reply(f"❌ Join @{FORCE_JOIN} first")
        return False

# ---------------- START ---------------- #
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    add_user(message.from_user.id)
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📯 Anime_UpdatesAU", url="https://t.me/Anime_UpdatesAU"),
         InlineKeyboardButton("💬 AU_Bot_Discussion", url="https://t.me/AU_Bot_Discussion")],
        [InlineKeyboardButton("🏠 Home", callback_data="home"),
         InlineKeyboardButton("ℹ️ About", callback_data="about"),
         InlineKeyboardButton("⚙ Help", callback_data="help")]
    ])
    photo_url = "https://graph.org/file/0e77ba48a8b7a3b09296f-362372bee0d84fd217.jpg"
    await message.reply_photo(photo=photo_url,
                              caption="👋 Welcome!\nUse /help to see all commands.",
                              reply_markup=buttons)

# ---------------- CALLBACKS ---------------- #
@bot.on_callback_query()
async def cb_handler(client, query):
    data = query.data
    if data == "home":
        await start_cmd(client, query.message)
    elif data == "help":
        text = (
            "/setcaption - Set file caption\n"
            "/seecaption - See current caption\n"
            "/removecaption - Remove caption\n"
            "/setthumbnail - Set thumbnail\n"
            "/viewthumbnail - View thumbnail\n"
            "/removethumbnail - Remove thumbnail\n"
            "/setmetadata - Set metadata\n"
            "/meta on/off - Enable/Disable metadata\n"
            "/setmedia video|document|audio - Choose media type"
        )
        await query.message.edit_text(text)
    elif data == "about":
        text = (
            "📌 **About Bot**\n"
            "Developer: @Mr_Mohammed_29\n"
            "Owner: You\n"
            "This bot can rename files up to 2GB, set captions, thumbnails, metadata and more."
        )
        await query.message.edit_text(text)

# ---------------- CAPTION ---------------- #
@bot.on_message(filters.command("setcaption") & filters.private)
async def set_caption_cmd(client, message):
    await message.reply("Send me the caption text...")
    # Wait for next message
    def check(m):
        return m.from_user.id == message.from_user.id and m.text
    m = await bot.listen(message.chat.id, filters=filters.text & filters.private, timeout=120)
    set_caption(message.from_user.id, m.text)
    await m.reply("✅ Caption saved!")

@bot.on_message(filters.command("seecaption") & filters.private)
async def see_caption_cmd(client, message):
    cap = get_caption(message.from_user.id)
    if cap:
        await message.reply(f"Current caption:\n{cap}")
    else:
        await message.reply("No caption set.")

@bot.on_message(filters.command("removecaption") & filters.private)
async def remove_caption_cmd(client, message):
    set_caption(message.from_user.id, None)
    await message.reply("✅ Caption removed!")

# ---------------- THUMBNAIL ---------------- #
@bot.on_message(filters.command("setthumbnail") & filters.private)
async def set_thumb_cmd(client, message):
    await message.reply("Send me the thumbnail image...")
    m = await bot.listen(message.chat.id, filters=filters.photo & filters.private, timeout=120)
    path = f"thumbnails/{message.from_user.id}.jpg"
    await m.download(path)
    set_thumb(message.from_user.id, path)
    await m.reply("✅ Thumbnail saved!")

@bot.on_message(filters.command("viewthumbnail") & filters.private)
async def view_thumb_cmd(client, message):
    path = get_thumb(message.from_user.id)
    if path:
        await message.reply_photo(path)
    else:
        await message.reply("No thumbnail set.")

@bot.on_message(filters.command("removethumbnail") & filters.private)
async def remove_thumb_cmd(client, message):
    set_thumb(message.from_user.id, None)
    await message.reply("✅ Thumbnail removed!")

# ---------------- METADATA ---------------- #
@bot.on_message(filters.command("setmetadata") & filters.private)
async def set_metadata_cmd(client, message):
    user_id = message.from_user.id
    USER_METADATA[user_id] = {}
    lines = message.text.split("\n")[1:]
    for line in lines:
        if "=" in line:
            key, value = line.split("=", 1)
            USER_METADATA[user_id][key.strip().lower()] = value.strip()
    await message.reply("✅ Metadata saved!")

@bot.on_message(filters.command("meta") & filters.private)
async def toggle_metadata_cmd(client, message):
    user_id = message.from_user.id
    if "on" in message.text.lower():
        META_ENABLED[user_id] = True
        await message.reply("🟢 Metadata enabled")
    elif "off" in message.text.lower():
        META_ENABLED[user_id] = False
        await message.reply("🔴 Metadata disabled")

# ---------------- SET MEDIA ---------------- #
@bot.on_message(filters.command("setmedia") & filters.private)
async def set_media_cmd(client, message):
    parts = message.text.split()
    if len(parts) != 2 or parts[1] not in ["video", "document", "audio"]:
        return await message.reply("Usage: /setmedia video|document|audio")
    set_media(message.from_user.id, parts[1])
    await message.reply(f"✅ Media mode set to {parts[1]}")

# ---------------- FILE HANDLER ---------------- #
@bot.on_message(filters.video | filters.document | filters.audio)
async def file_handler(client, message):
    if not await force_join_check(client, message):
        return

    user_id = message.from_user.id
    add_user(user_id)

    status = await message.reply("📥 Downloading...")
    start_time = time.time()

    file_path = await message.download(
        file_name=f"downloads/{user_id}_{int(time.time())}",
        progress=progress,
        progress_args=(status, start_time, "📥 Downloading")
    )

    # Metadata processing
    if META_ENABLED.get(user_id, True):
        metadata = USER_METADATA.get(user_id, {})
        if not metadata:
            metadata = METADATA_DEFAULT
        await status.edit("🛠 Applying metadata...")
        output_path = file_path + "_meta.mp4"
        cmd = ["ffmpeg", "-y", "-i", file_path]
        for key, value in metadata.items():
            cmd.extend(["-metadata", f"{key}={value}"])
        cmd.extend(["-codec", "copy", output_path])
        process = subprocess.run(cmd)
        if process.returncode == 0:
            os.remove(file_path)
            file_path = output_path

    # Upload
    mode = get_media(user_id) or "document"
    await status.edit("📤 Uploading...")
    start_time = time.time()
    if mode == "video":
        await client.send_video(message.chat.id, file_path, progress=progress, progress_args=(status, start_time, "📤 Uploading"))
    elif mode == "audio":
        await client.send_audio(message.chat.id, file_path, progress=progress, progress_args=(status, start_time, "📤 Uploading"))
    else:
        await client.send_document(message.chat.id, file_path, progress=progress, progress_args=(status, start_time, "📤 Uploading"))
    os.remove(file_path)
    await status.delete()

# ---------------- RUN ---------------- #
if __name__ == "__main__":
    bot.run()
