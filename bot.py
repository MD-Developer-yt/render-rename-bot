import os
import time
import subprocess
import threading
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database as db
from web import run  # web.py file

# ---------------- ENVIRONMENT ---------------- #
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

# ---------------- PROGRESS ---------------- #
progress_cache = {}

async def progress(current, total, message, start):
    now = time.time()

    if message.id in progress_cache:
        if now - progress_cache[message.id] < 2:
            return

    progress_cache[message.id] = now

    diff = now - start
    percentage = current * 100 / total
    speed = current / diff if diff > 0 else 0
    eta = int((total - current) / speed) if speed > 0 else 0

    bar_length = 20
    filled = int(bar_length * current / total)

    bar = "⬢" * filled + "⬡" * (bar_length - filled)

    text = (
        f"{bar}\n\n"
        f"⚡ **Progress:** {percentage:.2f}%\n"
        f"📦 **Done:** {current / (1024*1024):.2f} MB / {total / (1024*1024):.2f} MB\n"
        f"🚀 **Speed:** {speed / (1024*1024):.2f} MB/s\n"
        f"⏳ **ETA:** {eta//60:02d}:{eta%60:02d}"
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

# ---------------- CALLBACK HANDLER ---------------- #
@bot.on_callback_query()
async def callbacks(client, query):
    uid = query.from_user.id
    data = query.data

    # HELP
    if data == "help":
        await query.message.edit_text(
            "**Bot Commands**\n\n"
            "/setcaption - Set caption\n"
            "/setthumbnail - Reply to photo\n"
            "/setmedia - Select media type\n"
            "/setmetadata - Set metadata\n"
            "/status - Bot stats\n"
            "/broadcast - Broadcast message [Admin]",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="home")]])
        )
    # ABOUT
    elif data == "about":
        await query.message.edit_text(
            "**Auto Rename Bot**\n\n"
            "Supports:\n• Rename Files\n• Metadata\n• Thumbnail\n• Caption\n\n"
            "Channel: @Anime_UpdatesAU",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="home")]])
        )
    # METADATA
    elif data == "meta":
        status = db.get_metadata_status(uid)
        await query.message.edit_text(
            f"Metadata is {'✅ ON' if status else '❌ OFF'}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ON", callback_data="meta_on"), InlineKeyboardButton("OFF", callback_data="meta_off")],
                [InlineKeyboardButton("🔙 Back", callback_data="home")]
            ])
        )
    elif data == "meta_on":
        db.set_metadata_status(uid, True)
        await query.answer("Metadata Enabled")
    elif data == "meta_off":
        db.set_metadata_status(uid, False)
        await query.answer("Metadata Disabled")
    # BACK
    elif data == "home":
        await query.message.edit_text("👋 Welcome Back", reply_markup=start_buttons())
    # MEDIA
    elif data.startswith("media_"):
        mode = data.split("_")[1]
        db.set_media(uid, mode)
        await query.answer(f"Media set to {mode}")
        await query.message.edit_text(f"✅ Media Mode set to **{mode}**")

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
async def set_thumbnail(client, message):
    if message.reply_to_message and message.reply_to_message.photo:
        os.makedirs("thumbs", exist_ok=True)
        path = f"thumbs/{message.from_user.id}.jpg"
        await message.reply_to_message.download(path)
        db.set_thumb(message.from_user.id, path)
        await message.reply("✅ Thumbnail saved")
    else:
        await message.reply("Reply to a photo to set thumbnail")

# ---------------- SET MEDIA ---------------- #
@bot.on_message(filters.command("setmedia") & filters.private)
async def set_media_cmd(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎥 Video", callback_data="media_video"),
         InlineKeyboardButton("📁 File", callback_data="media_document"),
         InlineKeyboardButton("🎵 Audio", callback_data="media_audio")]
    ])
    await message.reply_text("Select Upload Mode:", reply_markup=buttons)

# ---------------- SET METADATA ---------------- #
@bot.on_message(filters.command("setmetadata") & filters.private)
async def set_metadata_cmd(client, message):
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
@bot.on_message(filters.command("status") & filters.private)
async def status_cmd(client, message):
    users = db.total_users()
    await message.reply_text(f"📊 Bot Status\n\nTotal Users: {users}")

# ---------------- BROADCAST ---------------- #
@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(client, message):
    if not message.reply_to_message:
        await message.reply("Reply to a message to broadcast")
        return
    users = db.get_users()
    success = fail = 0
    for user in users:
        try:
            await message.reply_to_message.copy(user)
            success += 1
        except:
            fail += 1
    await message.reply_text(f"✅ Broadcast Done\nSuccess: {success}\nFailed: {fail}")

# ---------------- FILE HANDLER ---------------- #

@bot.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def file_handler(client, message):

    user_id = message.from_user.id

    media = message.document or message.video or message.audio

    if not media:
        return

    msg = await message.reply_text("📥 Downloading file...")

    file_path = await message.download()

    await msg.edit("⚙ Processing file...")

    filename = os.path.basename(file_path)
    new_name = "AU_" + filename
    new_path = os.path.join(os.path.dirname(file_path), new_name)

    os.rename(file_path, new_path)

    # Metadata settings
    meta_title = "@Anime_UpdatesAU"
    meta_author = "@Anime_UpdatesAU"
    meta_artist = "@Anime_UpdatesAU"
    meta_audio = "@Anime_UpdatesAU"
    meta_video = "@Anime_UpdatesAU"
    meta_sub = "@Anime_UpdatesAU"

    output = "metadata_" + new_name

    cmd = [
        "ffmpeg",
        "-i", new_path,
        "-map", "0",
        "-c", "copy",
        "-metadata", f"title={meta_title}",
        "-metadata", f"author={meta_author}",
        "-metadata", f"artist={meta_artist}",
        "-metadata", f"audio={meta_audio}",
        "-metadata", f"video={meta_video}",
        "-metadata", f"subtitle={meta_sub}",
        output
    ]

    subprocess.run(cmd)

    caption = db.get_caption(user_id)
    thumb = db.get_thumbnail(user_id)
    media_mode = db.get_media(user_id)

    await msg.edit("📤 Uploading file...")

    if media_mode == "video":
        await client.send_video(
            chat_id=user_id,
            video=output,
            caption=caption,
            thumb=thumb
        )

    elif media_mode == "audio":
        await client.send_audio(
            chat_id=user_id,
            audio=output,
            caption=caption
        )

    else:
        await client.send_document(
            chat_id=user_id,
            document=output,
            caption=caption,
            thumb=thumb
        )

    os.remove(new_path)
    os.remove(output)

    await msg.delete()
# ---------------- RUN BOT ---------------- #
if __name__ == "__main__":
    threading.Thread(target=run).start()  # Start web.py for Render keep-alive
    print("Bot Started...")
    bot.run()
