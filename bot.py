import os
import time
import asyncio
import threading
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import *
from math import ceil

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
START_PIC = "https://graph.org/file/0e77ba48a8b7a3b09296f-362372bee0d84fd217.jpg"

os.makedirs("downloads", exist_ok=True)
os.makedirs("thumbnails", exist_ok=True)

PROGRESS_BAR = """\n
<b>🔗 Size :</b> {1} | {2}
<b>⏳️ Done :</b> {0}%
<b>🚀 Speed :</b> {3}/s
<b>⏰️ ETA :</b> {4}
"""

bot = Client("rename-render-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------------- PROGRESS ---------------- #
async def progress(current, total, msg, start, action="Processing"):
    now = time.time()
    diff = now - start
    if diff == 0: diff = 1
    percent = (current / total) * 100
    speed = current / diff
    eta = ceil((total - current) / speed)
    current_size = f"{current / 1024 / 1024:.2f} MB"
    total_size = f"{total / 1024 / 1024:.2f} MB"
    text = PROGRESS_BAR.format(round(percent,2), current_size, total_size, f"{speed/1024/1024:.2f} MB", eta)
    try:
        await msg.edit(text)
    except: pass

# ---------------- START ---------------- #
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

# ---------------- CALLBACK ---------------- #
@bot.on_callback_query()
async def cb_handler(client, query):
    data = query.data
    uid = query.from_user.id

    if data == "start":
        await start_cmd(client, query.message)
    elif data == "help":
        await query.message.edit_text(
            "📖 HELP\n\nCommands:\n/setcaption\n/seecaption\n/removecaption\n/setthumbnail\n/viewthumbnail\n/removethumbnail\n/setmetadata\n/meta on/off\n/setmedia video|audio|document",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="start")]])
        )
    elif data == "about":
        await query.message.edit_text(
            "ℹ ABOUT\nDeveloper: @Mr_Mohammed_29\nBot can rename 2GB files with captions, thumbnails, and metadata.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="start")]])
        )

# ---------------- CAPTION / THUMB / MEDIA ---------------- #
@bot.on_message(filters.private & filters.command("setcaption"))
async def set_caption_cmd(client, message):
    uid = message.from_user.id
    text = message.text.split(maxsplit=1)
    if len(text) < 2: return await message.reply("Usage: /setcaption Your caption")
    set_caption(uid, text[1])
    await message.reply("✅ Caption saved.")

@bot.on_message(filters.private & filters.command("seecaption"))
async def see_caption_cmd(client, message):
    uid = message.from_user.id
    cap = get_caption(uid)
    await message.reply(f"📄 Caption: {cap}" if cap else "No caption set.")

@bot.on_message(filters.private & filters.command("removecaption"))
async def remove_caption_cmd(client, message):
    remove_caption(message.from_user.id)
    await message.reply("✅ Caption removed.")

@bot.on_message(filters.private & filters.command("setthumbnail"))
async def set_thumbnail_cmd(client, message):
    uid = message.from_user.id
    if not message.photo: return await message.reply("Send a photo with this command")
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
    remove_thumb(message.from_user.id)
    await message.reply("✅ Thumbnail removed.")

@bot.on_message(filters.private & filters.command("setmedia"))
async def set_media_cmd(client, message):
    uid = message.from_user.id
    parts = message.text.split()
    if len(parts) < 2 or parts[1] not in ["video","audio","document"]:
        return await message.reply("Usage: /setmedia video|audio|document")
    set_media(uid, parts[1])
    await message.reply(f"✅ Media type set to {parts[1]}")

# ---------------- METADATA ---------------- #
@bot.on_message(filters.private & filters.command("setmetadata"))
async def set_metadata_cmd(client, message):
    uid = message.from_user.id
    lines = message.text.split("\n")[1:]
    meta = {}
    for line in lines:
        if "=" in line:
            key, val = line.split("=",1)
            meta[key.strip().lower()] = val.strip()
    set_metadata(uid, meta)
    await message.reply("✅ Metadata saved.")

@bot.on_message(filters.private & filters.command("meta"))
async def meta_toggle_cmd(client, message):
    uid = message.from_user.id
    if "on" in message.text.lower():
        db.set_metadata(uid, db.get_metadata(uid) or {})
        await message.reply("🟢 Metadata Enabled")
    elif "off" in message.text.lower():
        set_metadata(uid,{})
        await message.reply("🔴 Metadata Disabled")

# ---------------- FILE HANDLER ---------------- #
@bot.on_message(filters.private & (filters.video | filters.audio | filters.document))
async def file_handler(client, message):
    uid = message.from_user.id
    media = message.video or message.audio or message.document
    if media.file_size > MAX_FILE_SIZE: return await message.reply("❌ File > 2GB")
    status = await message.reply("📥 Downloading...")
    start = time.time()
    file_path = await message.download(file_name=f"downloads/{uid}_{int(time.time())}", progress=progress, progress_args=(status,start,"📥 Downloading..."))

    thumb = get_thumb(uid)
    meta = get_metadata(uid)
    meta_enabled = meta is not None

    # Apply metadata if enabled
    if meta_enabled and message.video:
        await status.edit("🛠 Applying metadata...")
        output_path = f"{file_path}_meta.mp4"
        cmd = ["ffmpeg","-y","-i",file_path]
        for k,v in meta.items():
            cmd += ["-metadata", f"{k}={v}"]
        cmd += ["-codec","copy",output_path]
        subprocess.run(cmd)
        file_path = output_path

    await status.edit("📤 Uploading...")
    mode = get_media(uid)
    if mode == "video":
        await client.send_video(message.chat.id,file_path,thumb=thumb,progress=progress,progress_args=(status,start,"📤 Uploading..."))
    elif mode == "audio":
        await client.send_audio(message.chat.id,file_path,progress=progress,progress_args=(status,start,"📤 Uploading..."))
    else:
        await client.send_document(message.chat.id,file_path,thumb=thumb,progress=progress,progress_args=(status,start,"📤 Uploading..."))
    os.remove(file_path)
    await status.delete()

# ---------------- RUN WEB ---------------- #
def run_web():
    from aiohttp import web
    async def handler(request): return web.Response(text="Bot is running!")
    async def start():
        app = web.Application()
        app.router.add_get("/", handler)
        port = int(os.environ.get("PORT",8080))
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner,"0.0.0.0",port)
        await site.start()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start())
    loop.run_forever()

if __name__=="__main__":
    threading.Thread(target=run_web).start()
    bot.run()
