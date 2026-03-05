import os
import time
import subprocess
import threading
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database as db
from web import run  # web.py server

# -------- ENV VARIABLES --------
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))

bot = Client(
    "render-rename-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=50
)

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

# -------- PROGRESS --------
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
    try: await message.edit(text)
    except: pass

# -------- BUTTONS --------
def start_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Updates", url="https://t.me/Anime_UpdatesAU"),
         InlineKeyboardButton("💬 Support", url="https://t.me/AU_Bot_Discussion")],
        [InlineKeyboardButton("❓ Help", callback_data="help"),
         InlineKeyboardButton("ℹ About", callback_data="about")],
        [InlineKeyboardButton("🏷 Metadata", callback_data="meta")]
    ])

# -------- START --------
@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    db.add_user(message.from_user.id)
    await message.reply_photo(
        photo="https://graph.org/file/0e77ba48a8b7a3b09296f-362372bee0d84fd217.jpg",
        caption=f"👋 Hello {message.from_user.first_name}\nSend file up to 2GB to rename.",
        reply_markup=start_buttons()
    )

# -------- HELP --------
@bot.on_callback_query(filters.regex("help"))
async def help_cb(client, query):
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="home")]])
    await query.message.edit_text(
        "**Bot Commands**\n\n"
        "/setmedia - Select upload type\n"
        "/setmetadata - Set metadata\n"
        "/setcaption - Set caption\n"
        "/setthumbnail - Set thumbnail\n"
        "/status - Bot stats\n"
        "/broadcast - [OWNER only]",
        reply_markup=buttons
    )

# -------- ABOUT --------
@bot.on_callback_query(filters.regex("about"))
async def about_cb(client, query):
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="home")]])
    await query.message.edit_text(
        "**Auto Rename Bot**\n\nSupports:\n• Rename Files\n• Metadata\n• Thumbnail\n• Caption\n\nChannel: @Anime_UpdatesAU",
        reply_markup=buttons
    )

# -------- BACK HOME --------
@bot.on_callback_query(filters.regex("home"))
async def back_home(client, query):
    await query.message.edit_text("👋 Welcome Back", reply_markup=start_buttons())

# -------- SET MEDIA --------
@bot.on_message(filters.command("setmedia") & filters.private)
async def set_media_buttons(client, message):
    buttons = InlineKeyboardMarkup([[
        InlineKeyboardButton("🎥 Video", callback_data="media_video"),
        InlineKeyboardButton("📁 File", callback_data="media_document"),
        InlineKeyboardButton("🎵 Audio", callback_data="media_audio")
    ]])
    await message.reply_text("Select Upload Mode:", reply_markup=buttons)

@bot.on_callback_query(filters.regex("media_"))
async def media_select(client, query):
    mode = query.data.split("_")[1]
    db.set_media(query.from_user.id, mode)
    await query.answer(f"Media set to {mode}")
    await query.message.edit_text(f"✅ Media Mode set to **{mode}**")

# -------- SET METADATA --------
@bot.on_message(filters.command("setmetadata"))
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

# -------- SET CAPTION --------
@bot.on_message(filters.command("setcaption") & filters.private)
async def set_caption(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2: return await message.reply("Send caption text")
    db.set_caption(message.from_user.id, parts[1])
    await message.reply("✅ Caption saved")

# -------- SET THUMBNAIL --------
@bot.on_message(filters.command("setthumbnail") & filters.private)
async def set_thumb(client, message):
    if message.reply_to_message and message.reply_to_message.photo:
        os.makedirs("thumbs", exist_ok=True)
        path = f"thumbs/{message.from_user.id}.jpg"
        await message.reply_to_message.download(path)
        db.set_thumb(message.from_user.id, path)
        await message.reply("✅ Thumbnail saved")

# -------- STATUS --------
@bot.on_message(filters.command("status"))
async def status_cmd(client, message):
    users = db.total_users()
    await message.reply_text(f"📊 **Bot Status**\n\nUsers : {users}")

# -------- BROADCAST --------
@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(client, message):
    if not message.reply_to_message:
        await message.reply("Reply to message to broadcast")
        return
    users = db.get_users()
    success = fail = 0
    for user in users:
        try: await message.reply_to_message.copy(user); success+=1
        except: fail+=1
    await message.reply_text(f"✅ Broadcast Done\n\nSuccess: {success}\nFailed: {fail}")

# -------- FILE RENAME --------
@bot.on_message(filters.document | filters.video | filters.audio)
async def rename_file(client, message):
    file = message.document or message.video or message.audio
    file_name = file.file_name
    new_name = "AU_" + file_name
    path = await message.download()
    caption = db.get_caption(message.from_user.id) or "Uploaded by @Anime_UpdatesAU"
    thumb = db.get_thumb(message.from_user.id)
    meta = db.get_metadata_status(message.from_user.id)
    if meta:
        output = "meta_" + new_name
        cmd = [
            "ffmpeg","-y","-i",path,"-map","0","-c","copy",
            "-metadata","title=@Anime_UpdatesAU",
            "-metadata","author=@Anime_UpdatesAU",
            "-metadata","artist=@Anime_UpdatesAU",
            "-metadata","audio=@Anime_UpdatesAU",
            "-metadata","video=@Anime_UpdatesAU",
            "-metadata","subtitle=@Anime_UpdatesAU",
            output
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(path)
        path = output
    await message.reply_document(path, file_name=new_name, caption=caption, thumb=thumb)
    if os.path.exists(path):
        os.remove(path)

# -------- RUN --------
if __name__ == "__main__":
    threading.Thread(target=run).start()
    print("Bot Started...")
    bot.run()
