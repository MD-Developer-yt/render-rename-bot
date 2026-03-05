import os
import time
import subprocess
import threading
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database as db
from web import run  # keep-alive web server

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH"))
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))  # your Telegram ID

bot = Client(
    "render-rename-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=50
)

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

# ---------------- PROGRESS BAR ---------------- #

progress_cache = {}

async def progress(current, total, message, start):
    now = time.time()
    if message.id in progress_cache and now - progress_cache[message.id] < 2:
        return
    progress_cache[message.id] = now
    diff = now - start
    percent = current * 100 / total
    speed = current / diff if diff > 0 else 0
    eta = int((total - current) / speed) if speed > 0 else 0
    filled = int(percent // 10)
    bar = "⬢" * filled + "⬡" * (10 - filled)
    text = f"{bar}\n\n📊 {percent:.1f}%\n🚀 {speed/1024/1024:.2f} MB/s\n⏳ ETA {eta//60:02d}:{eta%60:02d}"
    try:
        await message.edit(text)
    except:
        pass

# ---------------- START BUTTONS ---------------- #

def start_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Updates", url="https://t.me/Anime_UpdatesAU"),
            InlineKeyboardButton("💬 Support", url="https://t.me/AU_Bot_Discussion")
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="help"),
            InlineKeyboardButton("ℹ About", callback_data="about")
        ],
        [
            InlineKeyboardButton("🏷 Metadata", callback_data="meta")
        ]
    ])

# ---------------- START ---------------- #

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    db.add_user(message.from_user.id)
    await message.reply_photo(
        photo="https://graph.org/file/0e77ba48a8b7a3b09296f-362372bee0d84fd217.jpg",
        caption=f"👋 Hello {message.from_user.first_name}!\nSend file up to 2GB to rename.",
        reply_markup=start_buttons()
    )

# ---------------- HELP ---------------- #

@bot.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    text = """
📖 **Bot Help**
/setcaption - Set a custom caption
/setthumbnail - Reply to photo to set thumbnail
/setmedia - Choose media type (Video/File/Audio)
/setmetadata - Set metadata for files
/status - Bot stats
/broadcast - Send message to all users (Owner only)
"""
    await message.reply_text(text)

# ---------------- ABOUT ---------------- #

@bot.on_message(filters.command("about") & filters.private)
async def about_cmd(client, message):
    text = """
🤖 **AU Render Rename Bot**
⚡ Rename files up to 2GB
⚡ Caption & Thumbnail support
⚡ Metadata editor
Developer: @Mr_Mohammed_29
"""
    await message.reply_text(text)

# ---------------- STATUS ---------------- #

@bot.on_message(filters.command("status") & filters.private)
async def status_cmd(client, message):
    users = db.total_users()
    await message.reply_text(f"📊 **Bot Status**\n\nUsers: {users}")

# ---------------- BROADCAST ---------------- #

@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(client, message):
    if not message.reply_to_message:
        await message.reply("Reply to a message to broadcast")
        return
    users = db.get_users()
    success = 0
    fail = 0
    for user in users:
        try:
            await message.reply_to_message.copy(user)
            success += 1
        except:
            fail += 1
    await message.reply_text(f"✅ Broadcast Done\n\nSuccess: {success}\nFailed: {fail}")

# ---------------- SET CAPTION ---------------- #

@bot.on_message(filters.command("setcaption") & filters.private)
async def set_caption(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply("Send caption text after /setcaption")
    db.set_caption(message.from_user.id, parts[1])
    await message.reply("✅ Caption saved successfully!")

# ---------------- SET THUMBNAIL ---------------- #

@bot.on_message(filters.command("setthumbnail") & filters.private)
async def set_thumbnail(client, message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("❌ Reply to a photo with /setthumbnail to set your thumbnail")
        return
    os.makedirs("thumbs", exist_ok=True)
    path = f"thumbs/{message.from_user.id}.jpg"
    await message.reply_to_message.download(path)
    db.set_thumb(message.from_user.id, path)
    await message.reply("✅ Thumbnail saved successfully!")

# ---------------- SET MEDIA ---------------- #

@bot.on_message(filters.command("setmedia") & filters.private)
async def set_media(client, message):
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎥 Video", callback_data="media_video"),
            InlineKeyboardButton("📁 File", callback_data="media_document"),
            InlineKeyboardButton("🎵 Audio", callback_data="media_audio")
        ]
    ])
    await message.reply_text("Select Upload Mode:", reply_markup=buttons)

@bot.on_callback_query(filters.regex("media_"))
async def media_select(client, query):
    mode = query.data.split("_")[1]
    db.set_media(query.from_user.id, mode)
    await query.answer(f"✅ Media set to {mode}")
    await query.message.edit_text(f"✅ Media Mode set to **{mode}**")

# ---------------- SET METADATA ---------------- #

@bot.on_message(filters.command("setmetadata") & filters.private)
async def set_metadata(client, message):
    metadata = {
        "title": "@Anime_UpdatesAU",
        "author": "@Anime_UpdatesAU",
        "artist": "@Anime_UpdatesAU",
        "audio": "@Anime_UpdatesAU",
        "video": "@Anime_UpdatesAU",
        "subtitle": "@Anime_UpdatesAU"
    }
    db.set_metadata(message.from_user.id, metadata)
    await message.reply_text(
        "✅ Metadata Set Successfully\n\n"
        "Title : @Anime_UpdatesAU\n"
        "Author : @Anime_UpdatesAU\n"
        "Artist : @Anime_UpdatesAU\n"
        "Audio : @Anime_UpdatesAU\n"
        "Video : @Anime_UpdatesAU\n"
        "Subtitle : @Anime_UpdatesAU"
    )

# ---------------- FILE HANDLER ---------------- #

@bot.on_message(filters.document | filters.video | filters.audio)
async def file_handler(client, message):
    media = message.document or message.video or message.audio
    if media.file_size > MAX_FILE_SIZE:
        return await message.reply("❌ File exceeds 2GB")

    uid = message.from_user.id
    caption = db.get_caption(uid)
    thumb = db.get_thumb(uid)
    mode = db.get_media(uid)
    meta = db.get_metadata(uid)  # metadata dict

    status = await message.reply("Downloading...")
    start = time.time()
    file_path = await message.download(progress=progress, progress_args=(status,start))
    renamed = "renamed_" + os.path.basename(file_path)
    os.rename(file_path, renamed)
    output = renamed

    if meta:
        output = "meta_" + renamed
        cmd = [
            "ffmpeg","-y","-i",renamed,"-map","0","-c","copy",
            "-metadata",f"title={meta['title']}",
            "-metadata",f"author={meta['author']}",
            "-metadata",f"artist={meta['artist']}",
            "-metadata",f"audio={meta['audio']}",
            "-metadata",f"video={meta['video']}",
            "-metadata",f"subtitle={meta['subtitle']}",
            output
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(renamed)

    await status.edit("Uploading...")
    start = time.time()

    if mode == "video":
        await client.send_video(message.chat.id, video=output, caption=caption, thumb=thumb,
                                progress=progress, progress_args=(status,start))
    elif mode == "audio":
        await client.send_audio(message.chat.id, audio=output, caption=caption,
                                progress=progress, progress_args=(status,start))
    else:
        await client.send_document(message.chat.id, document=output, caption=caption, thumb=thumb,
                                   progress=progress, progress_args=(status,start))

    os.remove(output)
    await status.delete()

# ---------------- CALLBACK NAVIGATION ---------------- #

@bot.on_callback_query(filters.regex("help|about|home|meta"))
async def nav_callbacks(client, query):
    uid = query.from_user.id
    data = query.data

    if data == "help":
        await query.message.edit_text("📖 **Bot Help**\n/setcaption\n/setthumbnail\n/setmedia\n/setmetadata\n/status\n/broadcast",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="home")]]))
    elif data == "about":
        await query.message.edit_text("🤖 AU Render Rename Bot\nDeveloper: @Mr_Mohammed_29",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="home")]]))
    elif data == "home":
        await query.message.edit_text("👋 Welcome Back", reply_markup=start_buttons())
    elif data == "meta":
        status = db.get_metadata(uid)
        await query.message.edit_text(f"Metadata is {'✅ ON' if status else '❌ OFF'}")

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    threading.Thread(target=run).start()  # start web.py server
    print("Bot Started...")
    bot.run()
