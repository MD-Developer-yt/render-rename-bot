import os
import time
import math
import asyncio
import threading
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import *

# ---------------- BOT CONFIG ---------------- #
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
START_PIC = "https://graph.org/file/0e77ba48a8b7a3b09296f-362372bee0d84fd217.jpg"

os.makedirs("downloads", exist_ok=True)
os.makedirs("thumbnails", exist_ok=True)

# ---------------- BOT INSTANCE ---------------- #
bot = Client("rename-render-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------------- PROGRESS FUNCTION ---------------- #
async def progress(current, total, msg, start_time, action="Processing"):
    now = time.time()
    diff = now - start_time
    if diff == 0:
        diff = 1
    percent = current * 100 / total
    speed = current / diff
    eta = round((total - current) / speed)
    bar = "█" * int(percent / 5) + "░" * (20 - int(percent / 5))
    text = f"{action}\n[{bar}] {percent:.2f}%\nSpeed: {speed / 1024 / 1024:.2f} MB/s\nETA: {eta}s"
    try:
        await msg.edit(text)
    except:
        pass

# ---------------- START COMMAND ---------------- #
@bot.on_message(filters.private & filters.command("start"))
async def start_cmd(client, message):
    user = message.from_user
    add_user(user.id)
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Home", callback_data="start")],
        [InlineKeyboardButton("📢 Updates", url="https://t.me/Anime_UpdatesAU"),
         InlineKeyboardButton("💬 Support", url="https://t.me/AU_Bot_Discussion")],
        [InlineKeyboardButton("ℹ About", callback_data="about"),
         InlineKeyboardButton("🛠 Help", callback_data="help")]
    ])
    await message.reply_photo(START_PIC, caption=f"👋 Hello {user.first_name}\n\nWelcome to 2GB Rename Bot.", reply_markup=buttons)

# ---------------- CALLBACK HANDLER ---------------- #
@bot.on_callback_query()
async def cb_handler(client, query):
    data = query.data
    user_id = query.from_user.id

    if data == "start":
        await start_cmd(client, query.message)
    elif data == "help":
        await query.message.edit_text(
            "📖 HELP\n\nCommands:\n/setcaption\n/seecaption\n/removecaption\n/setthumbnail\n/viewthumbnail\n/removethumbnail\n/setmetadata\n/setmedia video|audio|document\n/meta on/off",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="start")]])
        )
    elif data == "about":
        await query.message.edit_text(
            "ℹ ABOUT\nDeveloper: @Mr_Mohammed_29\nThis bot can rename and upload 2GB files with captions, thumbnails, and metadata.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="start")]])
        )

# ---------------- CAPTION / THUMB / MEDIA ---------------- #
@bot.on_message(filters.private & filters.command("setcaption"))
async def set_caption_cmd(client, message):
    uid = message.from_user.id
    text = message.text.split(maxsplit=1)
    if len(text) < 2:
        return await message.reply("Usage: /setcaption Your caption here")
    set_caption(uid, text[1])
    await message.reply("✅ Caption saved.")

@bot.on_message(filters.private & filters.command("seecaption"))
async def see_caption_cmd(client, message):
    uid = message.from_user.id
    cap = get_caption(uid)
    await message.reply(f"📄 Caption: {cap}" if cap else "No caption set.")

@bot.on_message(filters.private & filters.command("removecaption"))
async def remove_caption_cmd(client, message):
    uid = message.from_user.id
    remove_caption(uid)
    await message.reply("✅ Caption removed.")

@bot.on_message(filters.private & filters.command("setthumbnail"))
async def set_thumbnail_cmd(client, message):
    uid = message.from_user.id
    if not message.photo:
        return await message.reply("Send a photo with this command")
    path = f"thumbnails/{uid}.jpg"
    await message.download(file_name=path)
    set_thumb(uid, path)
    await message.reply("✅ Thumbnail saved.")

@bot.on_message(filters.private & filters.command("viewthumbnail"))
async def view_thumbnail_cmd(client, message):
    uid = message.from_user.id
    thumb = get_thumb(uid)
    if thumb and os.path.exists(thumb):
        await message.reply_photo(thumb, caption="📸 Your Thumbnail")
    else:
        await message.reply("No thumbnail set.")

@bot.on_message(filters.private & filters.command("removethumbnail"))
async def remove_thumbnail_cmd(client, message):
    uid = message.from_user.id
    remove_thumb(uid)
    await message.reply("✅ Thumbnail removed.")

@bot.on_message(filters.private & filters.command("setmedia"))
async def set_media_cmd(client, message):
    uid = message.from_user.id
    parts = message.text.split()
    if len(parts) < 2 or parts[1] not in ["video", "audio", "document"]:
        return await message.reply("Usage: /setmedia video|audio|document")
    set_media(uid, parts[1])
    await message.reply(f"✅ Media type set to {parts[1]}")

# ---------------- FILE HANDLER ---------------- #
@bot.on_message(filters.private & (filters.video | filters.audio | filters.document))
async def file_handler(client, message):
    uid = message.from_user.id
    media = message.video or message.audio or message.document
    if media.file_size > MAX_FILE_SIZE:
        return await message.reply("❌ File exceeds 2GB limit")
    status = await message.reply("📥 Downloading...")
    start_time = time.time()
    file_path = await message.download(file_name=f"downloads/{uid}_{int(time.time())}", progress=progress, progress_args=(status, start_time))
    # apply thumbnail and metadata here if needed
    await status.edit("📤 Uploading...")
    mode = get_media(uid)
    if mode == "video":
        await client.send_video(message.chat.id, file_path, progress=progress, progress_args=(status, start_time))
    elif mode == "audio":
        await client.send_audio(message.chat.id, file_path, progress=progress, progress_args=(status, start_time))
    else:
        await client.send_document(message.chat.id, file_path, progress=progress, progress_args=(status, start_time))
    await status.delete()
    os.remove(file_path)

# ---------------- RUN WEB FOR RENDER ---------------- #
def run_web():
    from aiohttp import web
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
