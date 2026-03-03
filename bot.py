import os
import time
import math
import threading
import subprocess
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *

# ---------------- BOT SETUP ---------------- #

bot = Client(
    "render-rename-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---------------- MEMORY STORAGE ---------------- #

USERS = set()
CAPTIONS = {}
THUMBNAILS = {}
USER_METADATA = {}
META_ENABLED = {}
MEDIA_MODE = {}
START_TIME = time.time()

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB


# ---------------- PROGRESS FUNCTION ---------------- #

async def progress(current, total, message, start_time, action):

    now = time.time()
    diff = now - start_time

    if diff == 0:
        return

    percentage = current * 100 / total
    speed = current / diff
    eta = round((total - current) / speed) if speed > 0 else 0

    bar = "█" * int(percentage / 5) + "░" * (20 - int(percentage / 5))

    text = (
        f"{action}\n\n"
        f"[{bar}] {percentage:.2f}%\n"
        f"Speed: {speed / 1024 / 1024:.2f} MB/s\n"
        f"ETA: {eta}s"
    )

    try:
        await message.edit(text)
    except:
        pass


# ---------------- START (WELCOME + PHOTO + BUTTONS) ---------------- #

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):

    USERS.add(message.from_user.id)

    welcome_text = (
        f"👋 Hello {message.from_user.first_name}!\n\n"
        "🤖 Welcome to 2GB Rename Bot\n\n"
        "📂 Send video / document / audio\n\n"
        "Use /help to see all commands."
    )

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Updates", url="https://t.me/Anime_UpdatesAU"),
            InlineKeyboardButton("👤 Owner", url="https://t.me/Mr_Mohammed_29")
        ],
        [
            InlineKeyboardButton("⚙ Help", callback_data="help")
        ]
    ])

    # You can replace photo URL with your own image link
    photo_url = "https://graph.org/file/0e77ba48a8b7a3b09296f-362372bee0d84fd217.jpg"

    await message.reply_photo(
        photo=photo_url,
        caption=welcome_text,
        reply_markup=buttons
    )


# ---------------- HELP CALLBACK ---------------- #

@bot.on_callback_query(filters.regex("help"))
async def help_callback(client, callback_query):

    text = (
        "📖 USER COMMANDS\n\n"
        "/setcaption\n"
        "/removecaption\n"
        "/seecaption\n\n"
        "/setthumbnail\n"
        "/removethumbnail\n"
        "/viewthumbnail\n\n"
        "/setmetadata\n"
        "/meta on\n"
        "/meta off\n\n"
        "/setmedia video|document|audio"
    )

    await callback_query.message.edit_caption(text)


# ---------------- SET MEDIA ---------------- #

@bot.on_message(filters.command("setmedia") & filters.private)
async def set_media(client, message):

    if len(message.text.split()) < 2:
        return await message.reply("Usage: /setmedia video|document|audio")

    mode = message.text.split()[1].lower()

    if mode not in ["video", "document", "audio"]:
        return await message.reply("Choose: video / document / audio")

    MEDIA_MODE[message.from_user.id] = mode
    await message.reply(f"✅ Media mode set to {mode}")


# ---------------- META TOGGLE ---------------- #

@bot.on_message(filters.command("meta") & filters.private)
async def meta_toggle(client, message):

    user_id = message.from_user.id

    if "on" in message.text.lower():
        META_ENABLED[user_id] = True
        await message.reply("🟢 Metadata Enabled")

    elif "off" in message.text.lower():
        META_ENABLED[user_id] = False
        await message.reply("🔴 Metadata Disabled")


# ---------------- SET METADATA ---------------- #

@bot.on_message(filters.command("setmetadata") & filters.private)
async def set_metadata(client, message):

    if len(message.text.split()) == 1:
        return await message.reply(
            "Usage:\n\n"
            "/setmetadata\n"
            "title=Anime\n"
            "author=AU\n"
            "artist=Studio\n"
            "encoded_by=Anime Updates"
        )

    user_id = message.from_user.id
    USER_METADATA[user_id] = {}

    lines = message.text.split("\n")[1:]

    for line in lines:
        if "=" in line:
            key, value = line.split("=", 1)
            USER_METADATA[user_id][key.strip().lower()] = value.strip()

    await message.reply("✅ Metadata Saved")


# ---------------- FILE HANDLER ---------------- #

@bot.on_message(filters.video | filters.document | filters.audio)
async def handle_file(client, message):

    user_id = message.from_user.id
    media = message.video or message.document or message.audio

    if media.file_size > MAX_FILE_SIZE:
        return await message.reply("❌ File exceeds 2GB limit")

    status = await message.reply("📥 Starting Download...")
    start_time = time.time()

    file_path = await message.download(
        file_name=f"{user_id}_{int(time.time())}",
        progress=progress,
        progress_args=(status, start_time, "📥 Downloading...")
    )

    metadata = USER_METADATA.get(user_id)
    meta_status = META_ENABLED.get(user_id, True)

    if metadata and meta_status:

        await status.edit("🛠 Applying Metadata...")

        output_path = file_path + "_meta.mp4"
        cmd = ["ffmpeg", "-y", "-i", file_path]

        for key, value in metadata.items():
            cmd.extend(["-metadata", f"{key}={value}"])

        cmd.extend(["-codec", "copy", output_path])

        process = subprocess.run(cmd)

        if process.returncode == 0:
            os.remove(file_path)
            file_path = output_path

    await status.edit("📤 Uploading...")
    start_time = time.time()

    mode = MEDIA_MODE.get(user_id, "document")

    if mode == "video":
        await client.send_video(
            message.chat.id,
            file_path,
            supports_streaming=True,
            progress=progress,
            progress_args=(status, start_time, "📤 Uploading...")
        )

    elif mode == "audio":
        await client.send_audio(
            message.chat.id,
            file_path,
            progress=progress,
            progress_args=(status, start_time, "📤 Uploading...")
        )

    else:
        await client.send_document(
            message.chat.id,
            file_path,
            progress=progress,
            progress_args=(status, start_time, "📤 Uploading...")
        )

    os.remove(file_path)
    await status.delete()


# ---------------- WEB SERVER (RENDER) ---------------- #

def run_web():

    async def handler(request):
        return web.Response(text="Bot is running!")

    async def start():
        app = web.Application()
        app.router.add_get("/", handler)
        port = int(os.environ.get("PORT", 8080))
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()

    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start())
    loop.run_forever()


# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.run()
