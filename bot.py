# bot.py
import os
import time
import asyncio
import threading
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import add_user, set_caption, get_caption, set_thumb, get_thumb, set_media, get_media

# ---------------- BOT CONFIG ---------------- #
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))  # your Telegram ID as owner

bot = Client(
    "rename-render-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

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
    text = f"{action}\n[{bar}] {percentage:.2f}%\nSpeed: {speed/1024/1024:.2f} MB/s\nETA: {eta}s"
    try:
        await message.edit(text)
    except:
        pass

# ---------------- START ---------------- #
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user = message.from_user
    add_user(user.id)

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Anime Updates", url="https://t.me/Anime_UpdatesAU"),
         InlineKeyboardButton("💬 Support", url="https://t.me/AU_Bot_Discussion")],
        [InlineKeyboardButton("ℹ About", callback_data="about"),
         InlineKeyboardButton("🛠 Help", callback_data="help")]
    ])
    welcome_text = f"👋 Hello {user.first_name}!\n\nWelcome to the 2GB Rename Bot.\nSend video, audio, or document to rename."
    photo_url = "https://graph.org/file/0e77ba48a8b7a3b09296f-362372bee0d84fd217.jpg"
    await message.reply_photo(photo=photo_url, caption=welcome_text, reply_markup=kb)

# ---------------- CALLBACKS ---------------- #
@bot.on_callback_query()
async def cb_handler(c, q):
    data = q.data
    if data == "help":
        text = (
            "/setcaption - Set file caption\n"
            "/seecaption - View your caption\n"
            "/removecaption - Remove caption\n"
            "/setthumbnail - Set thumbnail\n"
            "/viewthumbnail - View thumbnail\n"
            "/removethumbnail - Remove thumbnail\n"
            "/setmetadata - Set metadata\n"
            "/setmedia video|audio|document - Select media type"
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="start")]])
        await q.message.edit(text=text, reply_markup=kb)
    elif data == "about":
        text = f"Developer: @Mr_Mohammed_29\nOwner: {OWNER_ID}\nThis bot renames files up to 2GB and applies metadata."
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="start")]])
        await q.message.edit(text=text, reply_markup=kb)

# ---------------- SET CAPTION ---------------- #
@bot.on_message(filters.command("setcaption") & filters.private)
async def set_caption_cmd(c, m):
    text = " ".join(m.text.split()[1:])
    if not text:
        return await m.reply("Usage: /setcaption your caption here")
    set_caption(m.from_user.id, text)
    await m.reply("✅ Caption saved!")

@bot.on_message(filters.command("seecaption") & filters.private)
async def see_caption_cmd(c, m):
    cap = get_caption(m.from_user.id)
    await m.reply(f"Your caption:\n{cap}" if cap else "You don't have a caption set.")

@bot.on_message(filters.command("removecaption") & filters.private)
async def remove_caption_cmd(c, m):
    set_caption(m.from_user.id, "")
    await m.reply("✅ Caption removed!")

# ---------------- SET THUMBNAIL ---------------- #
@bot.on_message(filters.command("setthumbnail") & filters.private)
async def set_thumb_cmd(c, m):
    if not m.reply_to_message or not m.reply_to_message.photo:
        return await m.reply("Reply to a photo with /setthumbnail")
    path = f"thumbnails/{m.from_user.id}.jpg"
    await m.reply_to_message.download(path)
    set_thumb(m.from_user.id, path)
    await m.reply("✅ Thumbnail saved!")

@bot.on_message(filters.command("viewthumbnail") & filters.private)
async def view_thumb_cmd(c, m):
    thumb = get_thumb(m.from_user.id)
    if thumb and os.path.exists(thumb):
        await m.reply_photo(thumb, caption="Your thumbnail")
    else:
        await m.reply("No thumbnail found.")

@bot.on_message(filters.command("removethumbnail") & filters.private)
async def remove_thumb_cmd(c, m):
    set_thumb(m.from_user.id, None)
    await m.reply("✅ Thumbnail removed!")

# ---------------- SET MEDIA ---------------- #
@bot.on_message(filters.command("setmedia") & filters.private)
async def set_media_cmd(c, m):
    if len(m.text.split()) < 2:
        return await m.reply("Usage: /setmedia video|audio|document")
    mode = m.text.split()[1].lower()
    if mode not in ["video", "audio", "document"]:
        return await m.reply("Choose: video / audio / document")
    set_media(m.from_user.id, mode)
    await m.reply(f"✅ Media set to {mode}")

# ---------------- SET METADATA ---------------- #
USER_METADATA = {}

@bot.on_message(filters.command("setmetadata") & filters.private)
async def set_metadata_cmd(c, m):
    lines = m.text.split("\n")[1:]  # skip command line
    if not lines:
        return await m.reply(
            "Usage:\n/setmetadata\n"
            "title=...\naudio=...\nauthor=...\nvideo=...\nsubtitle=...\nartist=...\nencoded_by=..."
        )
    USER_METADATA[m.from_user.id] = {}
    for line in lines:
        if "=" in line:
            key, value = line.split("=", 1)
            USER_METADATA[m.from_user.id][key.strip().lower()] = value.strip()
    await m.reply("✅ Metadata saved!")

# ---------------- FILE HANDLER ---------------- #
@bot.on_message(filters.video | filters.document | filters.audio)
async def handle_file(c, m):
    uid = m.from_user.id
    media = m.video or m.document or m.audio

    if media.file_size > MAX_FILE_SIZE:
        return await m.reply("❌ File exceeds 2GB limit")

    status = await m.reply("📥 Downloading...")
    start_time = time.time()
    file_path = await m.download(file_name=f"{uid}_{int(time.time())}",
                                 progress=progress,
                                 progress_args=(status, start_time, "📥 Downloading..."))

    metadata = USER_METADATA.get(uid)
    if metadata:
        await status.edit("🛠 Applying Metadata...")
        out_path = file_path + "_meta.mp4"
        cmd = ["ffmpeg", "-y", "-i", file_path]
        for k, v in metadata.items():
            cmd += ["-metadata", f"{k}={v}"]
        cmd += ["-codec", "copy", out_path]
        subprocess.run(cmd)
        os.remove(file_path)
        file_path = out_path

    await status.edit("📤 Uploading...")
    mode = get_media(uid)
    if mode == "video":
        await c.send_video(m.chat.id, file_path, supports_streaming=True,
                           progress=progress, progress_args=(status, time.time(), "📤 Uploading..."))
    elif mode == "audio":
        await c.send_audio(m.chat.id, file_path,
                           progress=progress, progress_args=(status, time.time(), "📤 Uploading..."))
    else:
        await c.send_document(m.chat.id, file_path,
                              progress=progress, progress_args=(status, time.time(), "📤 Uploading..."))
    os.remove(file_path)
    await status.delete()

# ---------------- RUN BOT ---------------- #
if __name__ == "__main__":
    bot.run()
