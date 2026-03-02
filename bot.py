import os, time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from database import *
from web import start as web_start

web_start()

bot = Client(
    "render-rename-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

os.makedirs("downloads", exist_ok=True)
os.makedirs("thumbnails", exist_ok=True)
os.makedirs("media", exist_ok=True)

METADATA_TEXT = """
Title : @Anime_UpdatesAU
Author : @Anime_UpdatesAU
Artist : @Anime_UpdatesAU
Audio : @Anime_UpdatesAU
Video : @Anime_UpdatesAU
Subtitle : @Anime_UpdatesAU
Encoded by : @Anime_UpdatesAU
"""

async def force_join(client, message):
    try:
        user = await client.get_chat_member(FORCE_JOIN, message.from_user.id)
        if user.status in ["left", "kicked"]:
            await message.reply(f"Join @{FORCE_JOIN} first")
            return False
        return True
    except:
        await message.reply(f"Join @{FORCE_JOIN} first")
        return False

def progress(current, total, msg, start):
    now = time.time()
    diff = now - start
    if diff % 5 == 0:
        percent = current * 100 / total
        bar = "█" * int(percent / 5) + "░" * (20 - int(percent / 5))
        text = f"**Uploading**\n{bar}\n{percent:.2f}%"
        try:
            msg.edit(text)
        except:
            pass

@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    if not await force_join(client, message): return
    add_user(message.from_user.id)

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("SET CAPTION", callback_data="setcap"),
         InlineKeyboardButton("SET THUMB", callback_data="setthumb")],
        [InlineKeyboardButton("SET MEDIA", callback_data="setmedia")],
        [InlineKeyboardButton("METADATA", callback_data="metadata")]
    ])
    await message.reply("**RENDER RENAME BOT**", reply_markup=kb)

@bot.on_callback_query(filters.regex("metadata"))
async def meta_cb(c, q):
    await q.message.reply(METADATA_TEXT)

@bot.on_callback_query(filters.regex("setmedia"))
async def setmedia_cb(c, q):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("VIDEO", callback_data="m_video"),
         InlineKeyboardButton("AUDIO", callback_data="m_audio")],
        [InlineKeyboardButton("FILE", callback_data="m_file")]
    ])
    await q.message.reply("Select Media Type", reply_markup=kb)

@bot.on_callback_query(filters.regex("m_"))
async def media_type(c, q):
    m = q.data.split("_")[1]
    set_media(q.from_user.id, m)
    await q.message.reply(f"Media set to: {m.upper()}")

@bot.on_callback_query(filters.regex("setcap"))
async def cap_cb(c, q):
    await q.message.reply("Send caption text")

@bot.on_callback_query(filters.regex("setthumb"))
async def thumb_cb(c, q):
    await q.message.reply("Send photo for thumbnail")

@bot.on_message(filters.text & filters.private)
async def text_handler(client, message):
    if not await force_join(client, message): return
    add_user(message.from_user.id)
    set_caption(message.from_user.id, message.text)
    await message.reply("Caption Saved")

@bot.on_message(filters.photo & filters.private)
async def thumb_handler(client, message):
    if not await force_join(client, message): return
    path = f"thumbnails/{message.from_user.id}.jpg"
    await message.download(path)
    set_thumb(message.from_user.id, path)
    await message.reply("Thumbnail Saved")

@bot.on_message(filters.document | filters.video | filters.audio)
async def rename(client, message):
    if not await force_join(client, message): return

    user_id = message.from_user.id
    add_user(user_id)

    msg = await message.reply("Downloading...")
    start = time.time()
    file = await message.download(
        file_name=f"downloads/{message.id}",
        progress=progress,
        progress_args=(msg, start)
    )

    new_name = "RENAMED_BY_@Anime_UpdatesAU"
    cap = get_caption(user_id)
    thumb = get_thumb(user_id)
    media_type = get_media(user_id)

    caption = cap if cap else METADATA_TEXT

    upload_msg = await message.reply("Uploading...")

    if media_type == "video":
        await client.send_video(
            message.chat.id,
            video=file,
            caption=caption,
            thumb=thumb,
            progress=progress,
            progress_args=(upload_msg, time.time())
        )
    elif media_type == "audio":
        await client.send_audio(
            message.chat.id,
            audio=file,
            caption=caption,
            thumb=thumb,
            progress=progress,
            progress_args=(upload_msg, time.time())
        )
    else:
        await client.send_document(
            message.chat.id,
            document=file,
            caption=caption,
            thumb=thumb,
            progress=progress,
            progress_args=(upload_msg, time.time())
        )

    os.remove(file)
    await msg.delete()
    await upload_msg.delete()

bot.run()
