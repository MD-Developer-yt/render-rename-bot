import os
import time
import threading
import subprocess
import asyncio
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import *

# ---------------- BOT SETUP ---------------- #
bot = Client(
    "rename-render-bot",
    api_id=int(os.environ.get("API_ID")),
    api_hash=os.environ.get("API_HASH"),
    bot_token=os.environ.get("BOT_TOKEN")
)

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
os.makedirs("downloads", exist_ok=True)
os.makedirs("thumbnails", exist_ok=True)

# ---------------- METADATA DEFAULT ---------------- #
METADATA_DEFAULT = {
    "title": "@Anime_UpdatesAU",
    "audio": "@Anime_UpdatesAU",
    "author": "@Anime_UpdatesAU",
    "video": "@Anime_UpdatesAU",
    "subtitle": "@Anime_UpdatesAU",
    "artist": "@Anime_UpdatesAU",
    "encoded_by": "@Anime_UpdatesAU"
}

# ---------------- HELPER FUNCTIONS ---------------- #
async def progress_bar(current, total, msg, start_time, action="Processing..."):
    now = time.time()
    elapsed = now - start_time
    if elapsed == 0:
        return
    percent = current * 100 / total
    speed = current / elapsed
    eta = round((total - current) / speed) if speed > 0 else 0
    bar = "█" * int(percent / 5) + "░" * (20 - int(percent / 5))
    text = f"{action}\n[{bar}] {percent:.2f}%\nSpeed: {speed/1024/1024:.2f} MB/s\nETA: {eta}s"
    try:
        await msg.edit(text)
    except:
        pass

# ---------------- START COMMAND ---------------- #
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user = message.from_user
    add_user(user.id)

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📯 Anime Updates", url="https://t.me/Anime_UpdatesAU"),
         InlineKeyboardButton("💁 Support", url="https://t.me/AU_Bot_Discussion")],
        [InlineKeyboardButton("🎛️ About", callback_data="about"),
         InlineKeyboardButton("🛠 Help", callback_data="help")]
    ])

    welcome_text = (
        f"👋 Hello {user.first_name}!\n"
        "Welcome to 2GB Rename Bot.\n"
        "Send video/document/audio to rename.\n"
        "Use the buttons below for About & Help."
    )

    photo_url = "https://graph.org/file/0e77ba48a8b7a3b09296f-362372bee0d84fd217.jpg"

    try:
        await message.reply_photo(
            photo=photo_url,
            caption=welcome_text,
            reply_markup=buttons
        )
    except:
        await message.reply_text(
            welcome_text,
            reply_markup=buttons
        )

# ---------------- CALLBACK HANDLER ---------------- #
@bot.on_callback_query()
async def cb_handler(client, query):
    data = query.data
    user = query.from_user
    home_btn = InlineKeyboardMarkup([[
        InlineKeyboardButton("🏠 Home", callback_data="start")
    ]])

    if data == "help":
        await query.message.edit_text(
            text=(
                "📖 USER COMMANDS\n\n"
                "/setcaption\n"
                "/removecaption\n"
                "/seecaption\n\n"
                "/setthumbnail\n"
                "/removethumbnail\n"
                "/viewthumbnail\n\n"
                "/setmetadata\n"
                "/meta on/off\n"
                "/setmedia video|document|audio\n"
                "/restart\n"
                "/status\n"
                "/users\n"
                "/broadcast"
            ),
            reply_markup=home_btn
        )

    elif data == "about":
        await query.message.edit_text(
            text=(
                "🤖 Bot Name: 2GB Rename Bot\n"
                "👨‍💻 Developer: @Mr_Mohammed_29\n"
                "📡 Library: Pyrogram\n"
                "⚡ Server: Render"
            ),
            reply_markup=home_btn
        )

# ---------------- SET CAPTION ---------------- #
@bot.on_message(filters.command("setcaption") & filters.private)
async def set_caption_cmd(client, message):
    text = " ".join(message.text.split()[1:])
    if not text:
        return await message.reply("Usage: /setcaption Your Caption Here")
    set_caption(message.from_user.id, text)
    await message.reply("✅ Caption saved.")

@bot.on_message(filters.command("removecaption") & filters.private)
async def remove_caption_cmd(client, message):
    set_caption(message.from_user.id, "")
    await message.reply("✅ Caption removed.")

@bot.on_message(filters.command("seecaption") & filters.private)
async def see_caption_cmd(client, message):
    cap = get_caption(message.from_user.id)
    await message.reply(f"📝 Caption: `{cap}`" if cap else "No caption set.")

# ---------------- SET THUMB ---------------- #
@bot.on_message(filters.command("setthumbnail") & filters.photo)
async def set_thumbnail_cmd(client, message):
    path = f"thumbnails/{message.from_user.id}.jpg"
    await message.download(path)
    set_thumb(message.from_user.id, path)
    await message.reply("✅ Thumbnail saved.")

@bot.on_message(filters.command("removethumbnail") & filters.private)
async def remove_thumbnail_cmd(client, message):
    set_thumb(message.from_user.id, None)
    await message.reply("✅ Thumbnail removed.")

@bot.on_message(filters.command("viewthumbnail") & filters.private)
async def view_thumbnail_cmd(client, message):
    thumb = get_thumb(message.from_user.id)
    if not thumb or not os.path.exists(thumb):
        return await message.reply("No thumbnail set.")
    await message.reply_photo(thumb, caption="🖼️ Your Thumbnail")

# ---------------- SET MEDIA ---------------- #
@bot.on_message(filters.command("setmedia") & filters.private)
async def set_media_cmd(client, message):
    if len(message.text.split()) < 2:
        return await message.reply("Usage: /setmedia video|document|audio")
    mode = message.text.split()[1].lower()
    if mode not in ["video", "document", "audio"]:
        return await message.reply("Choose: video / document / audio")
    set_media(message.from_user.id, mode)
    await message.reply(f"✅ Media mode set to {mode}")

# ---------------- SET METADATA ---------------- #
@bot.on_message(filters.command("setmetadata") & filters.private)
async def set_metadata_cmd(client, message):
    lines = message.text.split("\n")[1:]  # Skip first line /setmetadata
    meta = {}
    for line in lines:
        if "=" in line:
            k, v = line.split("=", 1)
            meta[k.strip().lower()] = v.strip()
    USER_METADATA[message.from_user.id] = meta
    await message.reply("✅ Metadata saved.")

# ---------------- META ON/OFF ---------------- #
@bot.on_message(filters.command("meta") & filters.private)
async def meta_toggle_cmd(client, message):
    uid = message.from_user.id
    if "on" in message.text.lower():
        META_ENABLED[uid] = True
        await message.reply("🟢 Metadata enabled")
    elif "off" in message.text.lower():
        META_ENABLED[uid] = False
        await message.reply("🔴 Metadata disabled")
    else:
        await message.reply("Usage: /meta on or /meta off")

# ---------------- FILE HANDLER ---------------- #
@bot.on_message(filters.video | filters.document | filters.audio)
async def handle_file(client, message):
    uid = message.from_user.id
    media = message.video or message.document or message.audio

    if media.file_size > MAX_FILE_SIZE:
        return await message.reply("❌ File exceeds 2GB limit")

    msg = await message.reply("📥 Downloading...")
    start_time = time.time()

    file_path = await message.download(
        file_name=f"downloads/{uid}_{int(time.time())}",
        progress=progress_bar,
        progress_args=(msg, start_time, "📥 Downloading...")
    )

    metadata = USER_METADATA.get(uid, METADATA_DEFAULT)
    meta_enabled = META_ENABLED.get(uid, True)

    if metadata and meta_enabled and file_path.endswith((".mp4", ".mkv")):
        await msg.edit("🛠 Applying metadata...")
        output_path = file_path + "_meta.mp4"
        cmd = ["ffmpeg", "-y", "-i", file_path]
        for k, v in metadata.items():
            cmd += ["-metadata", f"{k}={v}"]
        cmd += ["-codec", "copy", output_path]
        subprocess.run(cmd)
        os.remove(file_path)
        file_path = output_path

    await msg.edit("📤 Uploading...")
    start_time = time.time()
    mode = get_media(uid) or "document"
    if mode == "video":
        await client.send_video(message.chat.id, file_path,
                                supports_streaming=True,
                                progress=progress_bar,
                                progress_args=(msg, start_time, "📤 Uploading..."))
    elif mode == "audio":
        await client.send_audio(message.chat.id, file_path,
                                progress=progress_bar,
                                progress_args=(msg, start_time, "📤 Uploading..."))
    else:
        await client.send_document(message.chat.id, file_path,
                                   progress=progress_bar,
                                   progress_args=(msg, start_time, "📤 Uploading..."))
    os.remove(file_path)
    await msg.delete()

# ---------------- WEB SERVER ---------------- #
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

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start())
    loop.run_forever()

# ---------------- MAIN ---------------- #
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.run()
