import os
import time
import subprocess
import threading
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database as db
from web import run  # Make sure web.py is in the same folder

# ---------------- CONFIG ---------------- #
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))

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
    text = f"{bar}\n\n📊 {percent:.1f}%\n🚀 {speed/1024/1024:.2f} MB/s\n⏳ ETA {eta//60:02d}:{eta%60:02d}"
    try:
        await message.edit(text)
    except:
        pass

# ---------------- BUTTONS ---------------- #
def start_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Updates", url="https://t.me/Anime_UpdatesAU"),
         InlineKeyboardButton("💬 Support", url="https://t.me/AU_Bot_Discussion")],
        [InlineKeyboardButton("❓ Help", callback_data="help"),
         InlineKeyboardButton("ℹ About", callback_data="about")],
        [InlineKeyboardButton("🏷 Metadata", callback_data="meta")]
    ])

# ---------------- START ---------------- #
@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    db.add_user(message.from_user.id)
    await message.reply_photo(
        photo="https://graph.org/file/0e77ba48a8b7a3b09296f-362372bee0d84fd217.jpg",
        caption=f"👋 Hᴇʟʟᴏ {message.from_user.first_name}!\n"
                 "🤖 Wᴇʟᴄᴏᴍᴇ Tᴏ AU Rᴇɴᴅᴇʀ Rᴇɴᴀᴍᴇ Bᴏᴛ\n\n"
                 "• Tʜɪs Is Aɴ Aᴅᴠᴀɴᴄᴇᴅ Aɴᴅ Yᴇᴛ Pᴏᴡᴇʀꜰᴜʟ ɪʟʟᴇɢᴀʟ Rᴇɴᴀᴍᴇ Bᴏᴛ.\n"
                 "• Usɪɴɢ Tʜɪs Bᴏᴛ Yᴏᴜ Cᴀɴ Rᴇɴᴀᴍᴇ & Cʜᴀɴɢᴇ Tʜᴜᴍʙɴᴀɪʟ Oꜰ Yᴏᴜʀ Fɪʟᴇ.\n"
                 "• Yᴏᴜ Cᴀɴ Aʟsᴏ Cᴏɴᴠᴇʀᴛ Vɪᴅᴇᴏ Tᴏ Fɪʟᴇ & Fɪʟᴇ Tᴏ Vɪᴅᴇᴏ.\n\n"
                 "Thɪs Bᴏᴛ Wᴀs Cʀᴇᴀᴛᴇᴅ Bʏ :@Mr_Mohammed_29\n",
        reply_markup=start_buttons()
    )

# ---------------- HELP ---------------- #
@bot.on_callback_query(filters.regex("help"))
async def help_cb(client, query):
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="home")]])
    await query.message.edit_text(
        "**Bot Commands**\n\n"
        "/setmedia - Select upload type\n"
        "/setmetadata - Set default metadata\n"
        "/setcaption - Set your caption\n"
        "/setthumbnail - Set custom thumbnail\n"
        "/status - Bot status\n"
        "/broadcast - Broadcast message (Owner only)",
        reply_markup=buttons
    )

# ---------------- ABOUT ---------------- #
@bot.on_callback_query(filters.regex("about"))
async def about_cb(client, query):
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="home")]])
    await query.message.edit_text(
        "**Auto Rename Bot**\n\n"
        "• Rename Files up to 2GB\n"
        "• Thumbnail support\n"
        "• Caption support\n"
        "• Metadata editor\n\n"
        "Channel: @Anime_UpdatesAU",
        reply_markup=buttons
    )

# ---------------- BACK ---------------- #
@bot.on_callback_query(filters.regex("home"))
async def back_home(client, query):
    await query.message.edit_text(
        "👋 Hᴇʟʟᴏ {message.from_user.first_name}!\n"
            "🤖 Wᴇʟᴄᴏᴍᴇ Tᴏ AU Rᴇɴᴅᴇʀ Rᴇɴᴀᴍᴇ Bᴏᴛ\n\n"
            "• Tʜɪs Is Aɴ Aᴅᴠᴀɴᴄᴇᴅ Aɴᴅ Yᴇᴛ Pᴏᴡᴇʀꜰᴜʟ ɪʟʟᴇɢᴀʟ Rᴇɴᴀᴍᴇ Bᴏᴛ.\n"
            "• Usɪɴɢ Tʜɪs Bᴏᴛ Yᴏᴜ Cᴀɴ Rᴇɴᴀᴍᴇ & Cʜᴀɴɢᴇ Tʜᴜᴍʙɴᴀɪʟ Oꜰ Yᴏᴜʀ Fɪʟᴇ.\n"
            "• Yᴏᴜ Cᴀɴ Aʟsᴏ Cᴏɴᴠᴇʀᴛ Vɪᴅᴇᴏ Tᴏ Fɪʟᴇ & Fɪʟᴇ Tᴏ Vɪᴅᴇᴏ.\n\n"
            "Tʜɪs Bᴏᴛ Wᴀs Cʀᴇᴀᴛᴇᴅ Bʏ :@Mr_Mohammed_29\n",
        reply_markup=start_buttons()
    )

# ---------------- SET MEDIA ---------------- #
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

# ---------------- STATUS ---------------- #
@bot.on_message(filters.command("status") & filters.user(OWNER_ID))
async def status_cmd(client, message):
    users = db.total_users()
    await message.reply_text(f"📊 **Bot Status**\nUsers : {users}")

# ---------------- BROADCAST ---------------- #
@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(client, message):
    if not message.reply_to_message:
        return await message.reply("Reply to a message to broadcast.")
    users = db.get_users()
    success = fail = 0
    for user in users:
        try:
            await message.reply_to_message.copy(user)
            success += 1
        except:
            fail += 1
    await message.reply_text(f"✅ Broadcast Done\nSuccess: {success}\nFailed: {fail}")

# ---------------- SET CAPTION ---------------- #
@bot.on_message(filters.command("setcaption") & filters.private)
async def set_caption(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply("Send caption text")
    db.set_caption(message.from_user.id, parts[1])
    await message.reply("✅ Caption saved")

# ---------------- SET THUMBNAIL ---------------- #
@bot.on_message(filters.command("setthumbnail") & filters.private)
async def set_thumb(client, message):
    if message.reply_to_message and message.reply_to_message.photo:
        os.makedirs("thumbs", exist_ok=True)
        path = f"thumbs/{message.from_user.id}.jpg"
        await message.reply_to_message.download(path)
        db.set_thumb(message.from_user.id, path)
        await message.reply("✅ Thumbnail saved")

# ---------------- FILE HANDLER ---------------- #
@bot.on_message(filters.document | filters.video | filters.audio)
async def rename_file(client, message):
    media = message.document or message.video or message.audio
    if media.file_size > MAX_FILE_SIZE:
        return await message.reply("File exceeds 2GB")
    uid = message.from_user.id
    caption = db.get_caption(uid)
    thumb = db.get_thumb(uid)
    mode = db.get_media(uid)
    metadata = db.get_metadata(uid)
    status_msg = await message.reply("Downloading...")
    start = time.time()
    file_path = await message.download(progress=progress, progress_args=(status_msg, start))
    new_name = "AU_" + os.path.basename(file_path)
    os.rename(file_path, new_name)
    output = new_name
    if metadata:
        output_meta = "meta_" + new_name
        cmd = [
            "ffmpeg","-y","-i",new_name,"-map","0","-c","copy",
            "-metadata","title="+metadata["title"],
            "-metadata","author="+metadata["author"],
            "-metadata","artist="+metadata["artist"],
            "-metadata","audio="+metadata["audio"],
            "-metadata","video="+metadata["video"],
            "-metadata","subtitle="+metadata["subtitle"],
            output_meta
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(new_name)
        output = output_meta
    # Send file
    send_args = dict(
        chat_id=message.chat.id,
        caption=caption,
        thumb=thumb,
        progress=progress,
        progress_args=(status_msg,start)
    )
    if mode == "video":
        send_args["video"] = output
        await client.send_video(**send_args)
    elif mode == "audio":
        send_args["audio"] = output
        await client.send_audio(**send_args)
    else:
        send_args["document"] = output
        await client.send_document(**send_args)
    os.remove(output)
    await status_msg.delete()

# ---------------- RUN ---------------- #
if __name__ == "__main__":
    threading.Thread(target=run).start()  # start web server for Render
    print("Bot Started...")
    bot.run()
