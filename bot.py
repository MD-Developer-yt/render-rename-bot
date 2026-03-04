import os
import time
import subprocess
import threading
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database as db

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = Client("render-rename-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
META_VALUE = "@Anime_UpdatesAU"


# ---------------- HEX PROGRESS BAR ----------------
async def progress(current, total, message, start):
    now = time.time()
    diff = now - start
    if diff == 0:
        return

    percent = current * 100 / total
    speed = current / diff
    eta = int((total - current) / speed) if speed > 0 else 0

    filled = int(percent // 10)
    bar = "⬢" * filled + "⬡" * (10 - filled)

    text = (
        f"{bar}\n\n"
        f"📊 {percent:.2f}%\n"
        f"🚀 {speed/1024/1024:.2f} MB/s\n"
        f"⏳ ETA: {eta//60:02d}:{eta%60:02d}"
    )

    try:
        await message.edit(text)
    except:
        pass


# ---------------- START MENU ----------------
def start_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Updates", url="https://t.me/Anime_UpdatesAU"),
            InlineKeyboardButton("💬 Support", url="https://t.me/AU_Bot_Discussion")
        ],
        [
            InlineKeyboardButton("ℹ Help", callback_data="help"),
            InlineKeyboardButton("👤 About", callback_data="about")
        ]
    ])


@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    db.add_user(message.from_user.id)

    await message.reply_photo(
        photo="https://graph.org/file/0e77ba48a8b7a3b09296f-362372bee0d84fd217.jpg",
        caption=(
            f"👋 Hᴇʟʟᴏ {message.from_user.first_name}!\n"
            "🤖 Wᴇʟᴄᴏᴍᴇ Tᴏ AU Rᴇɴᴅᴇʀ Rᴇɴᴀᴍᴇ Bᴏᴛ\n\n"
            "• Tʜɪs Is Aɴ Aᴅᴠᴀɴᴄᴇᴅ Aɴᴅ Yᴇᴛ Pᴏᴡᴇʀꜰᴜʟ ɪʟʟᴇɢᴀʟ Rᴇɴᴀᴍᴇ Bᴏᴛ.\n"
            "• Usɪɴɢ Tʜɪs Bᴏᴛ Yᴏᴜ Cᴀɴ Rᴇɴᴀᴍᴇ & Cʜᴀɴɢᴇ Tʜᴜᴍʙɴᴀɪʟ Oꜰ Yᴏᴜʀ Fɪʟᴇ.\n"
            "• Yᴏᴜ Cᴀɴ Aʟsᴏ Cᴏɴᴠᴇʀᴛ Vɪᴅᴇᴏ Tᴏ Fɪʟᴇ & Fɪʟᴇ Tᴏ Vɪᴅᴇᴏ.\n\n"
            "ʜɪs Bᴏᴛ Wᴀs Cʀᴇᴀᴛᴇᴅ Bʏ :@Mr_Mohammed_29\n"
        ),
        reply_markup=start_buttons()
    )


# ---------------- ABOUT COMMAND ----------------
@bot.on_message(filters.command("about") & filters.private)
async def about_cmd(client, message):
    await message.reply_text(
        "🤖 Bot: **AU Render Rename Bot**\n"
        "📕 Library : Pyrogram\n"
        "✏️ Language : Python 3\n"
        "💾 Database : Mongo DB\n"
        "👨‍💻 Developer : @Mr_Mohammed_29\n"
        "📢 Updates @Anime_UpdatesAU\n"
        "💬 Support : @AU_Bot_Discussion\n"
        "📊 Build Version : @BotsServerDead",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        )
    )


# ---------------- CALLBACK HANDLER ----------------
@bot.on_callback_query()
async def callbacks(client, query):

    if query.data == "help":
        await query.message.edit_caption(
            caption=(
                "📖 **Help Menu**\n\n"
                "/setcaption - Set custom caption\n"
                "/setthumbnail - Reply to photo\n"
                "/setmedia video|document|audio\n\n"
                "Send file after setting options."
            ),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
            )
        )

    elif query.data == "about":
        await query.message.edit_caption(
            caption=(
                "🤖 Bot: **AU Render Rename Bot**\n"
                "📕 Library : Pyrogram\n"
                "✏️ Language : Python 3\n"
                "💾 Database : Mongo DB\n"
                "👨‍💻 Developer : @Mr_Mohammed_29\n"
                "📢 Updates @Anime_UpdatesAU\n"
                "💬 Support : @AU_Bot_Discussion\n"
                "📊 Build Version : @BotsServerDead"
            ),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
            )
        )

    elif query.data == "back":
        await query.message.edit_caption(
            caption="🤖 Welcome Back!\nSend file to start.",
            reply_markup=start_buttons()
        )


# ---------------- SETTINGS ----------------
@bot.on_message(filters.command("setcaption") & filters.private)
async def set_caption(client, message):
    db.set_caption(message.from_user.id, " ".join(message.text.split()[1:]))
    await message.reply("Caption saved.")


@bot.on_message(filters.command("setthumbnail") & filters.private)
async def set_thumb(client, message):
    if message.reply_to_message and message.reply_to_message.photo:
        os.makedirs("thumbs", exist_ok=True)
        path = f"thumbs/{message.from_user.id}.jpg"
        await message.reply_to_message.download(path)
        db.set_thumb(message.from_user.id, path)
        await message.reply("Thumbnail saved.")


@bot.on_message(filters.command("setmedia") & filters.private)
async def set_media(client, message):
    mode = message.text.split()[1].lower()
    if mode in ["video", "document", "audio"]:
        db.set_media(message.from_user.id, mode)
        await message.reply("Media updated.")
    else:
        await message.reply("Use video/document/audio")


# ---------------- FILE HANDLER ----------------
@bot.on_message(filters.video | filters.document | filters.audio)
async def handle_file(client, message):
    media = message.video or message.document or message.audio

    if media.file_size > MAX_FILE_SIZE:
        return await message.reply("File exceeds 2GB.")

    uid = message.from_user.id
    caption = db.get_caption(uid)
    thumb = db.get_thumb(uid)
    mode = db.get_media(uid)

    status = await message.reply("Processing...")
    start = time.time()

    file_path = await message.download(progress=progress, progress_args=(status, start))
    renamed = "renamed_" + os.path.basename(file_path)
    os.rename(file_path, renamed)

    # ----- APPLY FIXED METADATA -----
    output = "meta_" + renamed

    cmd = [
        "ffmpeg", "-y",
        "-i", renamed,
        "-map", "0",
        "-c", "copy",
        "-metadata", f"title={META_VALUE}",
        "-metadata", f"author={META_VALUE}",
        "-metadata", f"artist={META_VALUE}",
        "-metadata", f"audio={META_VALUE}",
        "-metadata", f"video={META_VALUE}",
        "-metadata", f"subtitle={META_VALUE}",
        output
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(renamed)

    start = time.time()

    send_args = dict(
        chat_id=message.chat.id,
        caption=caption,
        thumb=thumb,
        progress=progress,
        progress_args=(status, start)
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
    await status.delete()


# ---------------- RUN BOT ----------------
if __name__ == "__main__":
    from web import run
    threading.Thread(target=run).start()
    bot.run()

#Don't Remove Credits 
#Supports Group @AU_Bot_Discussion 
#Telegram Channel @Anime_UpdatesAU
#Developer @Mr_Mohammed_29
