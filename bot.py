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

bot = Client(
    "render-rename-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=50
)

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024


# ---------------- PROGRESS ---------------- #

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

    text = (
        f"{bar}\n\n"
        f"📊 {percent:.1f}%\n"
        f"🚀 {speed/1024/1024:.2f} MB/s\n"
        f"⏳ ETA: {eta//60:02d}:{eta%60:02d}"
    )

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
            InlineKeyboardButton("🏷 Metadata", callback_data="meta_menu")
        ]
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
                 "Tʜɪs Bᴏᴛ Wᴀs Cʀᴇᴀᴛᴇᴅ Bʏ :@Mr_Mohammed_29\n",
        reply_markup=start_buttons()
    )


# ---------------- HELP ---------------- #

HELP_TEXT = """
📖 Help Menu

/setcaption - Set custom caption
/setthumbnail - Reply to photo
/setmedia video|document|audio
/metadata - Toggle metadata
"""


# ---------------- ABOUT ---------------- #

ABOUT_TEXT = """
"🤖 Bot: **AU Render Rename Bot**\n"
"📕 Library : Pyrogram\n"
"✏️ Language : Python 3\n"
"💾 Database : Mongo DB\n"
"👨‍💻 Developer : @Mr_Mohammed_29\n"
"📢 Updates : @Anime_UpdatesAU\n"
"💬 Support : @AU_Bot_Discussion\n"
"📊 Build Version : @BotsServerDead"
"""


# ---------------- METADATA COMMAND ---------------- #

@bot.on_message(filters.command("metadata") & filters.private)
async def metadata_cmd(client, message):

    status = db.get_metadata_status(message.from_user.id)

    await message.reply_text(
        f"Metadata is {'✅ ON' if status else '❌ OFF'}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ ON", callback_data="meta_on"),
                InlineKeyboardButton("❌ OFF", callback_data="meta_off")
            ]
        ])
    )


# ---------------- CALLBACK ---------------- #

@bot.on_callback_query()
async def callbacks(client, query):

    uid = query.from_user.id

    if query.data == "help":

        await query.message.edit_caption(
            caption=HELP_TEXT,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
            )
        )

    elif query.data == "about":

        await query.message.edit_caption(
            caption=ABOUT_TEXT,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
            )
        )

    elif query.data == "meta_menu":

        status = db.get_metadata_status(uid)

        await query.message.edit_caption(
            caption=f"Metadata is {'✅ ON' if status else '❌ OFF'}",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ ON", callback_data="meta_on"),
                    InlineKeyboardButton("❌ OFF", callback_data="meta_off")
                ],
                [
                    InlineKeyboardButton("🔙 Back", callback_data="back")
                ]
            ])
        )

    elif query.data == "meta_on":

        db.set_metadata_status(uid, True)
        await query.answer("Metadata Enabled")

    elif query.data == "meta_off":

        db.set_metadata_status(uid, False)
        await query.answer("Metadata Disabled")

    elif query.data == "back":

        await query.message.edit_caption(
            caption="👋 Welcome!\nSend file to rename.",
            reply_markup=start_buttons()
        )


# ---------------- SETTINGS ---------------- #

@bot.on_message(filters.command("setcaption") & filters.private)
async def set_caption(client, message):

    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        return await message.reply("Send caption text.")

    db.set_caption(message.from_user.id, parts[1])

    await message.reply("Caption saved")


@bot.on_message(filters.command("setthumbnail") & filters.private)
async def set_thumb(client, message):

    if message.reply_to_message and message.reply_to_message.photo:

        os.makedirs("thumbs", exist_ok=True)

        path = f"thumbs/{message.from_user.id}.jpg"

        await message.reply_to_message.download(path)

        db.set_thumb(message.from_user.id, path)

        await message.reply("Thumbnail saved")


@bot.on_message(filters.command("setmedia") & filters.private)
async def set_media(client, message):

    parts = message.text.split()

    if len(parts) < 2:
        return await message.reply("Use video/document/audio")

    mode = parts[1].lower()

    if mode in ["video", "document", "audio"]:

        db.set_media(message.from_user.id, mode)

        await message.reply("Media updated")

    else:

        await message.reply("Use video/document/audio")


# ---------------- FILE HANDLER ---------------- #

@bot.on_message(filters.video | filters.document | filters.audio)
async def handle_file(client, message):

    media = message.video or message.document or message.audio

    if media.file_size > MAX_FILE_SIZE:
        return await message.reply("File exceeds 2GB.")

    uid = message.from_user.id

    caption = db.get_caption(uid)

    thumb = db.get_thumb(uid)

    mode = db.get_media(uid)

    meta_status = db.get_metadata_status(uid)

    status = await message.reply("Downloading...")

    start = time.time()

    file_path = await message.download(
        progress=progress,
        progress_args=(status, start)
    )

    renamed = "renamed_" + os.path.basename(file_path)

    os.rename(file_path, renamed)

    output = renamed

    if meta_status:

        output = "meta_" + renamed

        cmd = [
            "ffmpeg", "-y",
            "-i", renamed,
            "-map", "0",
            "-c", "copy",
            "-metadata", "title=@Anime_UpdatesAU",
            "-metadata", "author=@Anime_UpdatesAU",
            "-metadata", "artist=@Anime_UpdatesAU",
            "-metadata", "audio=@Anime_UpdatesAU",
            "-metadata", "video=@Anime_UpdatesAU",
            "-metadata", "subtitle=@Anime_UpdatesAU",
            output
        ]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        os.remove(renamed)

    await status.edit("Uploading...")

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


# ---------------- RUN ---------------- #

if __name__ == "__main__":

    from web import run

    threading.Thread(target=run).start()

    bot.run()
