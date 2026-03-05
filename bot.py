import os
import time
import threading
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database as db
from web import run  # Make sure web.py is present

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", 123456789))  # Replace with your Telegram ID

bot = Client(
    "render-rename-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=50
)

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024
progress_cache = {}

# ---------------- Progress Bar ---------------- #
async def progress(current, total, message, start):
    now = time.time()
    if message.id in progress_cache:
        if now - progress_cache[message.id] < 2:
            return
    progress_cache[message.id] = now
    diff = now - start
    percent = current * 100 / total
    speed = current / diff if diff > 0 else 0
    eta = int((total - current) / speed) if speed > 0 else 0
    filled = int(percent // 10)
    bar = "⬢" * filled + "⬡" * (10 - filled)
    text = (
        f"{bar}\n\n"
        f"📊 {percent:.1f}%\n"
        f"🚀 {speed/1024/1024:.2f} MB/s\n"
        f"⏳ ETA {eta//60:02d}:{eta%60:02d}"
    )
    try:
        await message.edit(text)
    except: pass

# ---------------- Start Buttons ---------------- #
def start_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Updates", url="https://t.me/Anime_UpdatesAU"),
         InlineKeyboardButton("💬 Support", url="https://t.me/AU_Bot_Discussion")],
        [InlineKeyboardButton("❓ Help", callback_data="help"),
         InlineKeyboardButton("ℹ About", callback_data="about")],
        [InlineKeyboardButton("🏷 Metadata", callback_data="meta")]
    ])

# ---------------- Start Command ---------------- #
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    db.add_user(message.from_user.id)
    await message.reply_photo(
        photo="https://graph.org/file/0e77ba48a8b7a3b09296f-362372bee0d84fd217.jpg",
        caption=f"👋 Hello {message.from_user.first_name}\nSend file up to 2GB to rename.",
        reply_markup=start_buttons()
    )

# ---------------- Help, About, Back Buttons ---------------- #
@bot.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    text = """
**Bot Commands:**
/start - Start bot
/help - Show help
/about - About bot
/setcaption - Set caption
/see_caption - View caption
/del_caption - Delete caption
/setthumbnail - Set thumbnail
/viewthumb - View thumbnail
/delthumb - Delete thumbnail
/setmedia - Choose upload mode
/setmetadata - Set metadata
/status - Show bot status
/broadcast - Broadcast message [Owner Only]
/ping - Check bot latency
/donate - Support developer
"""
    await message.reply_text(text)

@bot.on_message(filters.command("ping") & filters.private)
async def ping_cmd(client, message):
    start = time.time()
    m = await message.reply_text("🏓 Pinging...")
    await m.edit(f"🏓 Pong!\nResponse Time: {(time.time() - start)*1000:.1f} ms")

@bot.on_message(filters.command("donate") & filters.private)
async def donate_cmd(client, message):
    await message.reply_text(
        "💖 Support the developer:\n"
        "• Telegram: @Mr_Mohammed_29\n"
        "• Channel: @Anime_UpdatesAU"
    )

@bot.on_message(filters.command("status") & filters.private)
async def status_cmd(client, message):
    users = db.total_users()
    await message.reply_text(f"📊 **Bot Status**\n\nUsers : {users}")

# ---------------- Media Buttons ---------------- #
@bot.on_message(filters.command("setmedia") & filters.private)
async def set_media_buttons(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎥 Video", callback_data="media_video"),
         InlineKeyboardButton("📁 File", callback_data="media_document"),
         InlineKeyboardButton("🎵 Audio", callback_data="media_audio")]
    ])
    await message.reply_text("Select Upload Mode:", reply_markup=buttons)

@bot.on_callback_query(filters.regex("media_"))
async def media_select(client, query):
    mode = query.data.split("_")[1]
    db.set_media(query.from_user.id, mode)
    await query.answer(f"Media set to {mode}")
    await query.message.edit_text(f"✅ Media Mode set to **{mode}**")

# ---------------- Metadata ---------------- #
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

# ---------------- Broadcast ---------------- #
@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(client, message):
    if not message.reply_to_message:
        return await message.reply("Reply to a message to broadcast")
    users = db.get_users()
    success = 0
    fail = 0
    for user in users:
        try: await message.reply_to_message.copy(user); success += 1
        except: fail += 1
    await message.reply_text(f"✅ Broadcast Done\nSuccess: {success}\nFailed: {fail}")

# ---------------- File Handler ---------------- #
@bot.on_message(filters.document | filters.video | filters.audio)
async def file_handler(client, message):
    media = message.document or message.video or message.audio
    file_name = getattr(media, "file_name", None) or f"{media.file_id}.dat"
    uid = message.from_user.id
    caption = db.get_caption(uid) or "Uploaded by @Anime_UpdatesAU"
    thumb = db.get_thumb(uid)
    mode = db.get_media(uid) or "document"
    meta = db.get_metadata_status(uid)

    status = await message.reply("Downloading...")
    start = time.time()
    file_path = await message.download(progress=progress, progress_args=(status, start))
    renamed = "AU_" + file_name
    os.rename(file_path, renamed)
    output = renamed

    if meta:
        output = "meta_" + renamed
        cmd = [
            "ffmpeg","-y","-i",renamed,"-map","0","-c","copy",
            "-metadata","title=@Anime_UpdatesAU",
            "-metadata","author=@Anime_UpdatesAU",
            "-metadata","artist=@Anime_UpdatesAU",
            "-metadata","audio=@Anime_UpdatesAU",
            "-metadata","video=@Anime_UpdatesAU",
            "-metadata","subtitle=@Anime_UpdatesAU",
            output
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(renamed)

    await status.edit("Uploading...")
    if mode == "video":
        await client.send_video(message.chat.id, video=output, caption=caption, thumb=thumb,
                                progress=progress, progress_args=(status, start))
    elif mode == "audio":
        await client.send_audio(message.chat.id, audio=output, caption=caption,
                                progress=progress, progress_args=(status, start))
    else:
        await client.send_document(message.chat.id, document=output, caption=caption, thumb=thumb,
                                   progress=progress, progress_args=(status, start))
    os.remove(output)
    await status.delete()

# ---------------- Callback Buttons ---------------- #
@bot.on_callback_query()
async def callbacks(client, query):
    data = query.data
    uid = query.from_user.id

    if data == "help":
        await query.message.edit_text(
            "**Bot Commands:**\n/setcaption, /setthumbnail, /setmedia, /setmetadata, /status, /broadcast",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="home")]])
        )
    elif data == "about":
        await query.message.edit_text(
            "🤖 Auto Rename Bot\nChannel: @Anime_UpdatesAU\nDeveloper: @Mr_Mohammed_29",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="home")]])
        )
    elif data == "meta":
        status = db.get_metadata_status(uid)
        await query.message.edit_text(f"Metadata is {'✅ ON' if status else '❌ OFF'}",
                                      reply_markup=InlineKeyboardMarkup([
                                          [InlineKeyboardButton("ON", callback_data="meta_on"),
                                           InlineKeyboardButton("OFF", callback_data="meta_off")],
                                          [InlineKeyboardButton("🔙 Back", callback_data="home")]
                                      ]))
    elif data == "meta_on":
        db.set_metadata_status(uid, True)
        await query.answer("Metadata Enabled")
    elif data == "meta_off":
        db.set_metadata_status(uid, False)
        await query.answer("Metadata Disabled")
    elif data == "home":
        await query.message.edit_text("👋 Welcome Back", reply_markup=start_buttons())

# ---------------- Run ---------------- #
if __name__ == "__main__":
    threading.Thread(target=run).start()
    print("Bot Started...")
    bot.run()
