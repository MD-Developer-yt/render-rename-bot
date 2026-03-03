import os
import time
import asyncio
import threading
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database as db
import sys

# ---------------- BOT CONFIG ---------------- #
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", 123456789))  # Set your Telegram user ID

bot = Client(
    "rename-render-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
os.makedirs("downloads", exist_ok=True)
os.makedirs("thumbnails", exist_ok=True)

START_TIME = time.time()

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

# ---------------- START COMMAND ---------------- #
@bot.on_message(filters.private & filters.command("start"))
async def start_cmd(client, message):
    db.add_user(message.from_user.id)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Anime Updates", url="https://t.me/Anime_UpdatesAU"),
         InlineKeyboardButton("💬 Support", url="https://t.me/AU_Bot_Discussion")],
        [InlineKeyboardButton("🎛 About", callback_data="about"),
         InlineKeyboardButton("🛠 Help", callback_data="help")]
    ])
    photo_url = "https://graph.org/file/0e77ba48a8b7a3b09296f-362372bee0d84fd217.jpg"
    await message.reply_photo(photo=photo_url, caption="👋 Welcome to 2GB Rename Bot!", reply_markup=kb)

# ---------------- CALLBACKS ---------------- #
@bot.on_callback_query()
async def cb_handler(client, query):
    data = query.data
    if data == "help":
        await query.message.edit_text(
            text="/setcaption\n/removecaption\n/seecaption\n/setthumbnail\n/removethumbnail\n/viewthumbnail\n/setmetadata\n/meta on/off\n/setmedia video|audio|document",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back", callback_data="start")]
            ])
        )
    elif data == "about":
        await query.message.edit_text(
            text="Developer: @Mr_Mohammed_29\nBot: 2GB Rename Bot\nFeatures: Rename, Metadata, Set Media, Thumbnail, Broadcast",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back", callback_data="start")]
            ])
        )

# ---------------- CAPTION ---------------- #
@bot.on_message(filters.command("setcaption") & filters.private)
async def set_caption(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /setcaption Your caption text")
    db.set_caption(message.from_user.id, message.text.split(None,1)[1])
    await message.reply("✅ Caption Saved")

@bot.on_message(filters.command("seecaption") & filters.private)
async def see_caption(client, message):
    cap = db.get_caption(message.from_user.id)
    await message.reply(f"📄 Caption:\n{cap}" if cap else "No caption set")

@bot.on_message(filters.command("removecaption") & filters.private)
async def remove_caption(client, message):
    db.remove_caption(message.from_user.id)
    await message.reply("✅ Caption Removed")

# ---------------- THUMBNAIL ---------------- #
@bot.on_message(filters.command("setthumbnail") & filters.private)
async def set_thumb(client, message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply("Reply to a photo with /setthumbnail")
    path = f"thumbnails/{message.from_user.id}.jpg"
    await message.reply_to_message.download(path)
    db.set_thumb(message.from_user.id, path)
    await message.reply("✅ Thumbnail Saved")

@bot.on_message(filters.command("viewthumbnail") & filters.private)
async def view_thumb(client, message):
    path = db.get_thumb(message.from_user.id)
    if path and os.path.exists(path):
        await message.reply_photo(path)
    else:
        await message.reply("No thumbnail set")

@bot.on_message(filters.command("removethumbnail") & filters.private)
async def remove_thumb(client, message):
    db.remove_thumb(message.from_user.id)
    await message.reply("✅ Thumbnail Removed")

# ---------------- MEDIA ---------------- #
@bot.on_message(filters.command("setmedia") & filters.private)
async def set_media(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /setmedia video|audio|document")
    mode = message.command[1].lower()
    if mode not in ["video","audio","document"]:
        return await message.reply("Choose: video|audio|document")
    db.set_media(message.from_user.id, mode)
    await message.reply(f"✅ Media set to {mode}")

# ---------------- METADATA ---------------- #
@bot.on_message(filters.command("setmetadata") & filters.private)
async def set_metadata(client, message):
    lines = message.text.split("\n")[1:]
    meta = {}
    for line in lines:
        if "=" in line:
            k,v = line.split("=",1)
            meta[k.strip().lower()] = v.strip()
    db.set_metadata(message.from_user.id, meta)
    await message.reply("✅ Metadata Saved")

@bot.on_message(filters.command("meta") & filters.private)
async def toggle_meta(client, message):
    if "on" in message.text.lower():
        db.toggle_meta(message.from_user.id, True)
        await message.reply("🟢 Metadata Enabled")
    elif "off" in message.text.lower():
        db.toggle_meta(message.from_user.id, False)
        await message.reply("🔴 Metadata Disabled")

# ---------------- FILE HANDLER ---------------- #
@bot.on_message(filters.video | filters.document | filters.audio)
async def handle_file(client, message):
    user_id = message.from_user.id
    media = message.video or message.document or message.audio
    if media.file_size > MAX_FILE_SIZE:
        return await message.reply("❌ File exceeds 2GB limit")
    status = await message.reply("📥 Downloading...")
    start_time = time.time()
    file_path = await message.download(
        file_name=f"downloads/{user_id}_{int(time.time())}",
        progress=progress,
        progress_args=(status, start_time, "📥 Downloading...")
    )
    meta = db.get_metadata(user_id)
    if meta and meta["meta_enabled"]:
        await status.edit("🛠 Applying Metadata...")
        output_path = file_path + "_meta.mp4"
        cmd = ["ffmpeg","-y","-i",file_path]
        for key in ["title","audio","author","video","subtitle","artist","encoded_by"]:
            if meta.get(key):
                cmd.extend(["-metadata", f"{key}={meta[key]}"])
        cmd.extend(["-codec","copy",output_path])
        subprocess.run(cmd)
        os.remove(file_path)
        file_path = output_path
    await status.edit("📤 Uploading...")
    mode = db.get_media(user_id)
    if mode == "video":
        await client.send_video(message.chat.id, file_path, progress=progress, progress_args=(status, time.time(), "📤 Uploading..."))
    elif mode == "audio":
        await client.send_audio(message.chat.id, file_path, progress=progress, progress_args=(status, time.time(), "📤 Uploading..."))
    else:
        await client.send_document(message.chat.id, file_path, progress=progress, progress_args=(status, time.time(), "📤 Uploading..."))
    os.remove(file_path)
    await status.delete()

# ---------------- ADMIN COMMANDS ---------------- #
def owner_only(func):
    async def wrapper(client, message):
        if message.from_user.id != OWNER_ID:
            return await message.reply("❌ You are not the owner")
        return await func(client, message)
    return wrapper

@bot.on_message(filters.command("broadcast") & filters.private)
@owner_only
async def broadcast(client, message):
    text = message.text.split(None,1)
    if len(text) < 2:
        return await message.reply("Usage: /broadcast Your message")
    all_users = db.get_all_users()
    for uid in all_users:
        try:
            await client.send_message(uid, text[1])
        except:
            continue
    await message.reply(f"✅ Broadcast sent to {len(all_users)} users")

@bot.on_message(filters.command("users") & filters.private)
@owner_only
async def users_count(client, message):
    all_users = db.get_all_users()
    await message.reply(f"Total Users: {len(all_users)}")

@bot.on_message(filters.command("status") & filters.private)
@owner_only
async def status(client, message):
    uptime = time.time() - START_TIME
    hrs, rem = divmod(int(uptime), 3600)
    mins, secs = divmod(rem, 60)
    all_users = db.get_all_users()
    await message.reply(f"Uptime: {hrs}h {mins}m {secs}s\nTotal Users: {len(all_users)}")

@bot.on_message(filters.command("restart") & filters.private)
@owner_only
async def restart(client, message):
    await message.reply("♻️ Restarting Bot...")
    os.execv(sys.executable, ['python3'] + sys.argv)

# ---------------- RUN ---------------- #
if __name__ == "__main__":
    bot.run()
