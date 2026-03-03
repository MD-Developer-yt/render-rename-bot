import os
import time
import asyncio
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import db
from config import Config

# ---------------- MEMORY ---------------- #

USER_CAPTION = {}
USER_THUMB = {}
USER_METADATA = {}
META_ENABLED = {}
MEDIA_MODE = {}

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
        f"Speed: {speed/1024/1024:.2f} MB/s\n"
        f"ETA: {eta}s"
    )

    try:
        await message.edit(text)
    except:
        pass


# ---------------- START ---------------- #

@Client.on_message(filters.private & filters.command("start"))
async def start(client, message):

    await db.add_user(client, message)

    text = f"""
👋 Hello {message.from_user.mention} !

🤖 Rename Render Bot

Send file after setting options.
"""

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📯 Updates", url="https://t.me/Anime_UpdatesAU"),
         InlineKeyboardButton("💬 Support", url="https://t.me/AU_Bot_Discussion")],
        [InlineKeyboardButton("🛠 Help", callback_data="help"),
         InlineKeyboardButton("🎛 About", callback_data="about")]
    ])

    await message.reply_text(text, reply_markup=buttons)


# ---------------- HELP ---------------- #

@Client.on_callback_query(filters.regex("help"))
async def help_cb(client, query):

    text = """
🛠 COMMANDS

/setcaption
/seecaption
/removecaption

/setthumbnail
/viewthumbnail
/removethumbnail

/setmetadata
/meta on
/meta off

/setmedia video|document|audio

/broadcast
/users
/status
/restart
"""

    await query.message.edit_text(text)


# ---------------- ABOUT ---------------- #

@Client.on_callback_query(filters.regex("about"))
async def about_cb(client, query):

    text = """
🎛 ABOUT BOT

Max Size: 2GB
Hosted: Render
Library: Pyrogram

Developer: @Mr_Mohammed
Updates: @Anime_UpdatesAU
Support: @AU_Bot_Discussion
"""

    await query.message.edit_text(text)


# ---------------- CAPTION ---------------- #

@Client.on_message(filters.command("setcaption"))
async def set_caption(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /setcaption Your caption")

    USER_CAPTION[message.from_user.id] = message.text.split(None, 1)[1]
    await message.reply("✅ Caption Saved")


@Client.on_message(filters.command("seecaption"))
async def see_caption(client, message):
    cap = USER_CAPTION.get(message.from_user.id)
    await message.reply(cap if cap else "❌ No caption set.")


@Client.on_message(filters.command("removecaption"))
async def remove_caption(client, message):
    USER_CAPTION.pop(message.from_user.id, None)
    await message.reply("🗑 Caption Removed")


# ---------------- THUMBNAIL ---------------- #

@Client.on_message(filters.command("setthumbnail"))
async def set_thumb(client, message):
    await message.reply("Send a photo to save as thumbnail.")


@Client.on_message(filters.photo)
async def save_thumb(client, message):
    file = await message.download()
    USER_THUMB[message.from_user.id] = file
    await message.reply("✅ Thumbnail Saved")


@Client.on_message(filters.command("viewthumbnail"))
async def view_thumb(client, message):
    thumb = USER_THUMB.get(message.from_user.id)
    if not thumb:
        return await message.reply("No thumbnail set.")
    await message.reply_photo(thumb)


@Client.on_message(filters.command("removethumbnail"))
async def remove_thumb(client, message):
    thumb = USER_THUMB.pop(message.from_user.id, None)
    if thumb and os.path.exists(thumb):
        os.remove(thumb)
    await message.reply("🗑 Thumbnail Removed")


# ---------------- METADATA ---------------- #

@Client.on_message(filters.command("setmetadata"))
async def set_metadata(client, message):

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
            k, v = line.split("=", 1)
            k = k.strip().lower()
            if k in allowed:
                USER_METADATA[user_id][allowed[k]] = v.strip()

    await message.reply("✅ Metadata Saved")


@Client.on_message(filters.command("meta"))
async def meta_toggle(client, message):
    if "on" in message.text.lower():
        META_ENABLED[message.from_user.id] = True
        await message.reply("🟢 Metadata Enabled")
    else:
        META_ENABLED[message.from_user.id] = False
        await message.reply("🔴 Metadata Disabled")


# ---------------- MEDIA MODE ---------------- #

@Client.on_message(filters.command("setmedia"))
async def set_media(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /setmedia video|document|audio")

    MEDIA_MODE[message.from_user.id] = message.command[1]
    await message.reply("✅ Media Mode Updated")


# ---------------- FILE HANDLER ---------------- #

@Client.on_message(filters.video | filters.document | filters.audio)
async def handle_file(client, message):

    media = message.video or message.document or message.audio

    if media.file_size > MAX_FILE_SIZE:
        return await message.reply("❌ File exceeds 2GB")

    status = await message.reply("📥 Downloading...")
    start_time = time.time()

    file = await message.download(
        progress=progress,
        progress_args=(status, start_time, "📥 Downloading...")
    )

    user_id = message.from_user.id

    if META_ENABLED.get(user_id, True) and USER_METADATA.get(user_id):
        await status.edit("Applying metadata...")
        output = file + "_meta.mp4"

        cmd = ["ffmpeg", "-y", "-i", file]

        for k, v in USER_METADATA[user_id].items():
            cmd += ["-metadata", f"{k}={v}"]

        cmd += ["-codec", "copy", output]
        subprocess.run(cmd)

        os.remove(file)
        file = output

    await status.edit("📤 Uploading...")
    start_time = time.time()

    caption = USER_CAPTION.get(user_id, "")
    thumb = USER_THUMB.get(user_id)
    mode = MEDIA_MODE.get(user_id, "document")

    if mode == "video":
        await client.send_video(
            message.chat.id,
            file,
            caption=caption,
            thumb=thumb,
            supports_streaming=True,
            progress=progress,
            progress_args=(status, start_time, "📤 Uploading...")
        )
    else:
        await client.send_document(
            message.chat.id,
            file,
            caption=caption,
            thumb=thumb,
            progress=progress,
            progress_args=(status, start_time, "📤 Uploading...")
        )

    os.remove(file)
    await status.delete()


# ---------------- USERS / STATUS ---------------- #

@Client.on_message(filters.command("users"))
async def users_count(client, message):
    users = await db.get_all_users()
    await message.reply(f"Total Users: {len(users)}")


@Client.on_message(filters.command("status"))
async def status_cmd(client, message):
    await message.reply("Bot Running Normally ✅")


# ---------------- BROADCAST ---------------- #

@Client.on_message(filters.command("broadcast"))
async def broadcast(client, message):

    if not message.reply_to_message:
        return await message.reply("Reply to a message to broadcast.")

    users = await db.get_all_users()

    for user in users:
        try:
            await message.reply_to_message.copy(user)
        except:
            pass

    await message.reply("Broadcast Completed.")


# ---------------- RESTART ---------------- #

@Client.on_message(filters.command("restart"))
async def restart_cmd(client, message):
    await message.reply("Restarting...")
    os.execl(sys.executable, sys.executable, *sys.argv)
