# bot.py
import os
import time
import threading
import subprocess
import asyncio
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import add_user, set_caption, get_caption, set_thumb, get_thumb, set_media, get_media

# ---------------- BOT SETUP ---------------- #
bot = Client(
    "rename-render-bot",
    api_id=int(os.environ.get("API_ID", 12345)),
    api_hash=os.environ.get("API_HASH", ""),
    bot_token=os.environ.get("BOT_TOKEN", "")
)

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

# ---------------- USER STORAGE ---------------- #
USER_METADATA = {}
META_ENABLED = {}

# ---------------- PROGRESS ---------------- #
async def progress(current, total, message, start_time, action):
    now = time.time()
    diff = now - start_time
    if diff == 0:
        return
    percentage = current * 100 / total
    speed = current / diff
    eta = round((total - current) / speed) if speed > 0 else 0
    bar = "█" * int(percentage / 5) + "░" * (20 - int(percentage / 5))
    text = f"{action}\n\n[{bar}] {percentage:.2f}%\nSpeed: {speed/1024/1024:.2f} MB/s\nETA: {eta}s"
    try:
        await message.edit(text)
    except:
        pass

# ---------------- START ---------------- #
@bot.on_message(filters.private & filters.command("start"))
async def start_cmd(client, message):
    add_user(message.from_user.id)
    welcome_text = (
        f"👋 Hello {message.from_user.first_name}!\n\n"
        "🤖 Welcome to 2GB Rename Bot\n"
        "📂 Send a video / audio / document to rename\n"
        "Use /help to see commands."
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Home", callback_data="start"),
         InlineKeyboardButton("🎛 About", callback_data="about")],
        [InlineKeyboardButton("🛠 Help", callback_data="help"),
         InlineKeyboardButton("📯 Support", url="https://t.me/AU_Bot_Discussion")],
        [InlineKeyboardButton("📢 Updates", url="https://t.me/Anime_UpdatesAU")]
    ])
    photo_url = "https://graph.org/file/0e77ba48a8b7a3b09296f-362372bee0d84fd217.jpg"
    await message.reply_photo(photo_url, caption=welcome_text, reply_markup=buttons)

# ---------------- CALLBACKS ---------------- #
@bot.on_callback_query()
async def cb_handler(client, query):
    data = query.data
    user_id = query.from_user.id

    if data == "start":
        await start_cmd(client, query.message)
    elif data == "help":
        text = (
            "📖 Commands:\n"
            "/setcaption - Set custom caption\n"
            "/seecaption - View caption\n"
            "/removecaption - Remove caption\n"
            "/setthumbnail - Set thumbnail\n"
            "/viewthumbnail - View thumbnail\n"
            "/removethumbnail - Remove thumbnail\n"
            "/setmetadata - Set metadata\n"
            "/meta on/off - Enable/Disable metadata\n"
            "/setmedia - Select media type (video/audio/document)\n"
            "/status - Bot uptime\n"
            "/users - Total users\n"
            "/broadcast - Send message to all users\n"
            "/restart - Restart bot\n"
        )
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="start")]])
        await query.message.edit(text=text, reply_markup=buttons)
    elif data == "about":
        text = (
            "🤖 Bot: AU Rename Bot\n"
            "💻 Developer: @Mr_Mohammed_29\n"
            "📦 Supports: 2GB Files\n"
            "📜 Metadata: Title, Audio, Author, Video, Subtitle, Artist, Encoded by"
        )
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="start")]])
        await query.message.edit(text=text, reply_markup=buttons)

# ---------------- CAPTION ---------------- #
@bot.on_message(filters.private & filters.command("setcaption"))
async def setcaption_cmd(client, message):
    if len(message.text.split()) < 2:
        return await message.reply("Usage: /setcaption Your caption here")
    text = message.text.split(None, 1)[1]
    set_caption(message.from_user.id, text)
    await message.reply("✅ Caption saved!")

@bot.on_message(filters.private & filters.command("seecaption"))
async def seecaption_cmd(client, message):
    cap = get_caption(message.from_user.id)
    await message.reply(f"💬 Your caption:\n{cap}" if cap else "No caption set.")

@bot.on_message(filters.private & filters.command("removecaption"))
async def removecaption_cmd(client, message):
    set_caption(message.from_user.id, "")
    await message.reply("✅ Caption removed.")

# ---------------- THUMBNAIL ---------------- #
@bot.on_message(filters.private & filters.command("setthumbnail"))
async def setthumb_cmd(client, message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply("Reply to a photo with /setthumbnail")
    path = f"thumbnails/{message.from_user.id}.jpg"
    await message.reply_to_message.download(path)
    set_thumb(message.from_user.id, path)
    await message.reply("✅ Thumbnail saved!")

@bot.on_message(filters.private & filters.command("viewthumbnail"))
async def viewthumb_cmd(client, message):
    thumb = get_thumb(message.from_user.id)
    if not thumb or not os.path.exists(thumb):
        return await message.reply("No thumbnail set.")
    await message.reply_photo(thumb, caption="🖼 Your thumbnail")

@bot.on_message(filters.private & filters.command("removethumbnail"))
async def removethumb_cmd(client, message):
    thumb = get_thumb(message.from_user.id)
    if thumb and os.path.exists(thumb):
        os.remove(thumb)
    set_thumb(message.from_user.id, "")
    await message.reply("✅ Thumbnail removed.")

# ---------------- METADATA ---------------- #
@bot.on_message(filters.private & filters.command("setmetadata"))
async def setmetadata_cmd(client, message):
    if len(message.text.splitlines()) < 2:
        return await message.reply(
            "Usage:\n/setmetadata\n"
            "title=...\naudio=...\nauthor=...\nvideo=...\nsubtitle=...\nartist=...\nencoded_by=..."
        )
    lines = message.text.splitlines()[1:]
    USER_METADATA[message.from_user.id] = {}
    for line in lines:
        if "=" in line:
            k, v = line.split("=", 1)
            USER_METADATA[message.from_user.id][k.strip().lower()] = v.strip()
    await message.reply("✅ Metadata saved!")

@bot.on_message(filters.private & filters.command("meta"))
async def meta_toggle(client, message):
    user_id = message.from_user.id
    if "on" in message.text.lower():
        META_ENABLED[user_id] = True
        await message.reply("🟢 Metadata enabled")
    elif "off" in message.text.lower():
        META_ENABLED[user_id] = False
        await message.reply("🔴 Metadata disabled")

# ---------------- MEDIA ---------------- #
@bot.on_message(filters.private & filters.command("setmedia"))
async def setmedia_cmd(client, message):
    if len(message.text.split()) < 2:
        return await message.reply("Usage: /setmedia video|document|audio")
    mode = message.text.split()[1].lower()
    if mode not in ["video", "document", "audio"]:
        return await message.reply("Choose: video / document / audio")
    set_media(message.from_user.id, mode)
    await message.reply(f"✅ Media set to {mode}")

# ---------------- FILE HANDLER ---------------- #
@bot.on_message(filters.document | filters.video | filters.audio)
async def handle_file(client, message):
    user_id = message.from_user.id
    media_obj = message.video or message.document or message.audio
    if media_obj.file_size > MAX_FILE_SIZE:
        return await message.reply("❌ File exceeds 2GB limit")

    status = await message.reply("📥 Starting download...")
    start_time = time.time()
    file_path = await message.download(
        file_name=f"{user_id}_{int(time.time())}",
        progress=progress,
        progress_args=(status, start_time, "📥 Downloading...")
    )

    # Apply metadata if enabled
    if META_ENABLED.get(user_id, True) and USER_METADATA.get(user_id):
        meta = USER_METADATA[user_id]
        await status.edit("🛠 Applying metadata...")
        output = file_path + "_meta.mp4"
        cmd = ["ffmpeg", "-y", "-i", file_path]
        for k, v in meta.items():
            cmd += ["-metadata", f"{k}={v}"]
        cmd += ["-codec", "copy", output]
        subprocess.run(cmd)
        os.remove(file_path)
        file_path = output

    await status.edit("📤 Uploading...")
    start_time = time.time()
    mode = get_media(user_id)

    if mode == "video":
        await client.send_video(message.chat.id, file_path, supports_streaming=True,
                                progress=progress, progress_args=(status, start_time, "📤 Uploading..."))
    elif mode == "audio":
        await client.send_audio(message.chat.id, file_path,
                                progress=progress, progress_args=(status, start_time, "📤 Uploading..."))
    else:
        await client.send_document(message.chat.id, file_path,
                                   progress=progress, progress_args=(status, start_time, "📤 Uploading..."))
    os.remove(file_path)
    await status.delete()

# ---------------- WEB SERVER ---------------- #
def run_web():
    async def handler(request):
        return web.Response(text="Bot is running!")

    async def start():
        app = web.Application()
        app.router.add_get("/", handler)
        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.environ.get("PORT", 8080))
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
