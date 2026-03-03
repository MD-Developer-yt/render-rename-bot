import asyncio

# Python 3.14 event loop fix
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import os
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from database import *

os.makedirs("downloads", exist_ok=True)
os.makedirs("thumbnails", exist_ok=True)

METADATA_TEXT = """
Title : @Anime_UpdatesAU
Author : @Anime_UpdatesAU
Artist : @Anime_UpdatesAU
Audio : @Anime_UpdatesAU
Video : @Anime_UpdatesAU
Subtitle : @Anime_UpdatesAU
Encoded by : @Anime_UpdatesAU
"""

bot = Client(
    "render-rename-bot",
    api_id=int(API_ID),
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---------------- FORCE JOIN ---------------- #

async def force_join(client, message):
    if not FORCE_JOIN:
        return True
    try:
        user = await client.get_chat_member(FORCE_JOIN, message.from_user.id)
        if user.status in ["left", "kicked"]:
            await message.reply(f"Join @{FORCE_JOIN} first")
            return False
        return True
    except:
        await message.reply(f"Join @{FORCE_JOIN} first")
        return False

# ---------------- PROGRESS ---------------- #

def progress(current, total, msg, start):
    now = time.time()
    if int(now - start) % 4 == 0:
        percent = current * 100 / total
        bar = "█" * int(percent / 5) + "░" * (20 - int(percent / 5))
        try:
            asyncio.create_task(
                msg.edit(f"Processing...\n{bar}\n{percent:.2f}%")
            )
        except:
            pass

# ---------------- START ---------------- #

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    if not await force_join(client, message):
        return

    add_user(message.from_user.id)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("SET CAPTION", callback_data="setcap"),
         InlineKeyboardButton("SET THUMB", callback_data="setthumb")],
        [InlineKeyboardButton("SET MEDIA", callback_data="setmedia")],
        [InlineKeyboardButton("METADATA", callback_data="metadata")]
    ])

    await message.reply("RENDER RENAME BOT", reply_markup=keyboard)

# ---------------- CALLBACKS ---------------- #

@bot.on_callback_query()
async def callbacks(client, query):
    data = query.data
    await query.answer()

    if data == "metadata":
        await query.message.reply(METADATA_TEXT)

    elif data == "setcap":
        await query.message.reply("Send caption text")

    elif data == "setthumb":
        await query.message.reply("Send photo for thumbnail")

    elif data == "setmedia":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("VIDEO", callback_data="m_video"),
             InlineKeyboardButton("AUDIO", callback_data="m_audio")],
            [InlineKeyboardButton("FILE", callback_data="m_document")]
        ])
        await query.message.reply("Select Media Type", reply_markup=keyboard)

    elif data.startswith("m_"):
        media_type = data.split("_")[1]
        set_media(query.from_user.id, media_type)
        await query.message.reply(f"Media set to: {media_type.upper()}")

# ---------------- SAVE CAPTION ---------------- #

@bot.on_message(filters.text & filters.private)
async def save_caption(client, message):
    if not await force_join(client, message):
        return
    set_caption(message.from_user.id, message.text)
    await message.reply("Caption Saved")

# ---------------- SAVE THUMB ---------------- #

@bot.on_message(filters.photo & filters.private)
async def save_thumb(client, message):
    if not await force_join(client, message):
        return
    path = f"thumbnails/{message.from_user.id}.jpg"
    await message.download(path)
    set_thumb(message.from_user.id, path)
    await message.reply("Thumbnail Saved")

# ---------------- RENAME ---------------- #

@bot.on_message(filters.document | filters.video | filters.audio)
async def rename_file(client, message):
    if not await force_join(client, message):
        return

    user_id = message.from_user.id
    add_user(user_id)

    msg = await message.reply("Downloading...")
    start = time.time()

    file_path = await message.download(
        file_name=f"downloads/{message.id}",
        progress=progress,
        progress_args=(msg, start)
    )

    caption = get_caption(user_id) or METADATA_TEXT
    thumb = get_thumb(user_id)
    media = get_media(user_id)

    upload_msg = await message.reply("Uploading...")

    if media == "video":
        await client.send_video(message.chat.id, file_path, caption=caption, thumb=thumb)
    elif media == "audio":
        await client.send_audio(message.chat.id, file_path, caption=caption, thumb=thumb)
    else:
        await client.send_document(message.chat.id, file_path, caption=caption, thumb=thumb)

    os.remove(file_path)
    await msg.delete()
    await upload_msg.delete()

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    print("Bot is starting...")
    bot.run()
