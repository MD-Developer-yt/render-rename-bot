import os
import time
import threading
import subprocess
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN

# ---------------- BOT SETUP ---------------- #

bot = Client(
    "rename-render-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---------------- MEMORY STORAGE ---------------- #

USERS = set()
USER_METADATA = {}
META_ENABLED = {}
MEDIA_MODE = {}
USER_CAPTION = {}
USER_THUMB = {}

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB


# ---------------- PROGRESS BAR ---------------- #

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


# ---------------- START ---------------- #

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):

    text = (
        f"👋 Hello {message.from_user.first_name}!\n\n"
        "🤖 Welcome to 2GB Rename Bot\n\n"
        "Send video / document / audio."
    )

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🏠 Home", callback_data="home"),
            InlineKeyboardButton("ℹ About", callback_data="about")
        ]
    ])

    photo_url = "https://graph.org/file/0e77ba48a8b7a3b09296f-362372bee0d84fd217.jpg"

    await message.reply_photo(photo_url, caption=text, reply_markup=buttons)


# ---------------- CALLBACKS ---------------- #

@bot.on_callback_query()
async def callback_handler(client, callback_query):

    if callback_query.data == "home":
        text = "🏠 Send your file to process."
    elif callback_query.data == "about":
        text = "ℹ 2GB Rename Bot\nSupports metadata, caption, thumbnail & media selection."
    else:
        return

    await callback_query.message.edit_caption(text)


# ---------------- CAPTION COMMANDS ---------------- #

@bot.on_message(filters.command("setcaption") & filters.private)
async def set_caption(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /setcaption Your Caption Here")

    USER_CAPTION[message.from_user.id] = message.text.split(None, 1)[1]
    await message.reply("✅ Caption Saved")


@bot.on_message(filters.command("seecaption") & filters.private)
async def see_caption(client, message):
    caption = USER_CAPTION.get(message.from_user.id)
    if not caption:
        return await message.reply("❌ No caption set.")
    await message.reply(f"📄 Your Caption:\n\n{caption}")


@bot.on_message(filters.command("removecaption") & filters.private)
async def remove_caption(client, message):
    USER_CAPTION.pop(message.from_user.id, None)
    await message.reply("🗑 Caption Removed")


# ---------------- THUMBNAIL COMMANDS ---------------- #

@bot.on_message(filters.command("setthumbnail") & filters.private)
async def set_thumbnail(client, message):
    await message.reply("📸 Send a photo to set as thumbnail.")


@bot.on_message(filters.photo & filters.private)
async def save_thumbnail(client, message):
    user_id = message.from_user.id
    file_path = await message.download()
    USER_THUMB[user_id] = file_path
    await message.reply("✅ Thumbnail Saved")


@bot.on_message(filters.command("viewthumbnail") & filters.private)
async def view_thumbnail(client, message):
    thumb = USER_THUMB.get(message.from_user.id)
    if not thumb:
        return await message.reply("❌ No thumbnail set.")
    await message.reply_photo(thumb)


@bot.on_message(filters.command("removethumbnail") & filters.private)
async def remove_thumbnail(client, message):
    thumb = USER_THUMB.pop(message.from_user.id, None)
    if thumb and os.path.exists(thumb):
        os.remove(thumb)
    await message.reply("🗑 Thumbnail Removed")


# ---------------- SET MEDIA ---------------- #

@bot.on_message(filters.command("setmedia") & filters.private)
async def set_media(client, message):

    if len(message.command) < 2:
        return await message.reply("Usage: /setmedia video|document|audio")

    mode = message.command[1].lower()

    if mode not in ["video", "document", "audio"]:
        return await message.reply("Choose: video / document / audio")

    MEDIA_MODE[message.from_user.id] = mode
    await message.reply(f"✅ Media mode set to {mode}")


# ---------------- METADATA ---------------- #

@bot.on_message(filters.command("setmetadata") & filters.private)
async def set_metadata(client, message):

    if len(message.text.split("\n")) == 1:
        return await message.reply(
            "/setmetadata\n"
            "Title=...\n"
            "Audio=...\n"
            "Author=...\n"
            "Video=...\n"
            "Subtitle=...\n"
            "Artist=...\n"
            "Encoded by=..."
        )

    user_id = message.from_user.id
    USER_METADATA[user_id] = {}

    allowed = {
        "title": "title",
        "audio": "comment",
        "author": "author",
        "video": "description",
        "subtitle": "lyrics",
        "artist": "artist",
        "encoded by": "encoder"
    }

    lines = message.text.split("\n")[1:]

    for line in lines:
        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip().lower()
            if key in allowed:
                USER_METADATA[user_id][allowed[key]] = value.strip()

    await message.reply("✅ Metadata Saved")


@bot.on_message(filters.command("meta") & filters.private)
async def toggle_meta(client, message):

    user_id = message.from_user.id

    if "on" in message.text.lower():
        META_ENABLED[user_id] = True
        await message.reply("🟢 Metadata Enabled")

    elif "off" in message.text.lower():
        META_ENABLED[user_id] = False
        await message.reply("🔴 Metadata Disabled")


# ---------------- FILE HANDLER ---------------- #

@bot.on_message(filters.video | filters.document | filters.audio)
async def handle_file(client, message):

    user_id = message.from_user.id
    media = message.video or message.document or message.audio

    if media.file_size > MAX_FILE_SIZE:
        return await message.reply("❌ File exceeds 2GB")

    status = await message.reply("📥 Downloading...")
    start_time = time.time()

    file_path = await message.download(
        progress=progress,
        progress_args=(status, start_time, "📥 Downloading...")
    )

    metadata = USER_METADATA.get(user_id)
    if metadata and META_ENABLED.get(user_id, True):

        await status.edit("🛠 Applying Metadata...")
        output = file_path + "_meta.mp4"
        cmd = ["ffmpeg", "-y", "-i", file_path]

        for k, v in metadata.items():
            cmd += ["-metadata", f"{k}={v}"]

        cmd += ["-codec", "copy", output]
        subprocess.run(cmd)

        os.remove(file_path)
        file_path = output

    await status.edit("📤 Uploading...")
    start_time = time.time()

    caption = USER_CAPTION.get(user_id, "")
    thumb = USER_THUMB.get(user_id)
    mode = MEDIA_MODE.get(user_id, "document")

    if mode == "video":
        await client.send_video(
            message.chat.id,
            file_path,
            caption=caption,
            thumb=thumb,
            supports_streaming=True,
            progress=progress,
            progress_args=(status, start_time, "📤 Uploading...")
        )

    elif mode == "audio":
        await client.send_audio(
            message.chat.id,
            file_path,
            caption=caption,
            progress=progress,
            progress_args=(status, start_time, "📤 Uploading...")
        )

    else:
        await client.send_document(
            message.chat.id,
            file_path,
            caption=caption,
            thumb=thumb,
            progress=progress,
            progress_args=(status, start_time, "📤 Uploading...")
        )

    os.remove(file_path)
    await status.delete()


# ---------------- RENDER WEB SERVER ---------------- #

def run_web():

    async def handler(request):
        return web.Response(text="Bot Running")

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


if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.run()
