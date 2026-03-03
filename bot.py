import os
import time
import threading
import asyncio
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import add_user, set_caption, get_caption, set_thumb, get_thumb, set_media, get_media
from config import API_ID, API_HASH, BOT_TOKEN

# ---------------- BOT ---------------- #
bot = Client(
    "rename-render-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

# ---------------- START COMMAND ---------------- #
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user = message.from_user
    add_user(user.id)

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📯 Anime Updates", url="https://t.me/Anime_UpdatesAU"),
         InlineKeyboardButton("💁 Support", url="https://t.me/AU_Bot_Discussion")],
        [InlineKeyboardButton("🎛️ About", callback_data="about"),
         InlineKeyboardButton("🛠 Help", callback_data="help")]
    ])
    await message.reply_text(
        f"👋 Hello {user.first_name}!\nWelcome to 2GB Rename Bot.\nSend video/document/audio to rename.",
        reply_markup=buttons
    )

# ---------------- CALLBACKS ---------------- #
@bot.on_callback_query(filters.regex("start"))
async def start_cb(c, q):
    await start_cmd(c, q.message)

@bot.on_callback_query(filters.regex("help"))
async def help_cb(c, q):
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="start")]])
    await q.message.edit_text(
        "/setcaption\n/seecaption\n/removecaption\n"
        "/setthumbnail\n/viewthumbnail\n/removethumbnail\n"
        "/setmedia video|document|audio\n/setmetadata\n/meta on/off",
        reply_markup=buttons
    )

@bot.on_callback_query(filters.regex("about"))
async def about_cb(c, q):
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="start")]])
    await q.message.edit_text(
        "About Bot:\nDeveloper: @Mr_Mohammed_29\nPurpose: Rename & upload files up to 2GB",
        reply_markup=buttons
    )

# ---------------- CAPTION COMMANDS ---------------- #
@bot.on_message(filters.command("setcaption") & filters.private)
async def setcaption_cmd(c, message):
    if len(message.text.split(maxsplit=1)) < 2:
        return await message.reply("Usage: /setcaption Your caption text")
    text = message.text.split(maxsplit=1)[1]
    set_caption(message.from_user.id, text)
    await message.reply("✅ Caption saved!")

@bot.on_message(filters.command("seecaption") & filters.private)
async def seecaption_cmd(c, message):
    caption = get_caption(message.from_user.id)
    await message.reply(f"Your caption: {caption}" if caption else "No caption set.")

@bot.on_message(filters.command("removecaption") & filters.private)
async def removecaption_cmd(c, message):
    set_caption(message.from_user.id, "")
    await message.reply("✅ Caption removed.")

# ---------------- THUMBNAIL COMMANDS ---------------- #
@bot.on_message(filters.command("setthumbnail") & filters.photo & filters.private)
async def setthumbnail_cmd(c, message):
    path = f"thumbnails/{message.from_user.id}.jpg"
    await message.download(path)
    set_thumb(message.from_user.id, path)
    await message.reply("✅ Thumbnail saved!")

@bot.on_message(filters.command("viewthumbnail") & filters.private)
async def viewthumbnail_cmd(c, message):
    thumb = get_thumb(message.from_user.id)
    if thumb and os.path.exists(thumb):
        await message.reply_photo(thumb)
    else:
        await message.reply("No thumbnail set.")

@bot.on_message(filters.command("removethumbnail") & filters.private)
async def removethumbnail_cmd(c, message):
    set_thumb(message.from_user.id, "")
    await message.reply("✅ Thumbnail removed.")

# ---------------- SET MEDIA ---------------- #
@bot.on_message(filters.command("setmedia") & filters.private)
async def setmedia_cmd(c, message):
    if len(message.text.split()) < 2:
        return await message.reply("Usage: /setmedia video|document|audio")
    mode = message.text.split()[1].lower()
    if mode not in ["video", "document", "audio"]:
        return await message.reply("Choose: video / document / audio")
    set_media(message.from_user.id, mode)
    await message.reply(f"✅ Media mode set to {mode}")

# ---------------- FILE HANDLER ---------------- #
@bot.on_message(filters.video | filters.document | filters.audio)
async def handle_file(client, message):
    media = message.video or message.document or message.audio
    user_id = message.from_user.id

    if media.file_size > MAX_FILE_SIZE:
        return await message.reply("❌ File exceeds 2GB limit")

    status = await message.reply("📥 Downloading...")
    start_time = time.time()
    file_path = await message.download(file_name=f"downloads/{user_id}_{message.message_id}")

    # Upload
    mode = get_media(user_id)
    await status.edit("📤 Uploading...")

    if mode == "video":
        await client.send_video(message.chat.id, file_path, progress=progress_bar, progress_args=(status, start_time))
    elif mode == "audio":
        await client.send_audio(message.chat.id, file_path, progress=progress_bar, progress_args=(status, start_time))
    else:
        await client.send_document(message.chat.id, file_path, progress=progress_bar, progress_args=(status, start_time))

    os.remove(file_path)
    await status.delete()

# ---------------- PROGRESS BAR ---------------- #
async def progress_bar(current, total, msg, start_time):
    now = time.time()
    if int(now - start_time) % 3 == 0:
        percent = current * 100 / total
        bar = "█" * int(percent / 5) + "░" * (20 - int(percent / 5))
        try:
            await msg.edit(f"Processing...\n[{bar}] {percent:.2f}%")
        except:
            pass

# ---------------- WEB SERVER ---------------- #
def run_web():
    async def handler(request):
        return web.Response(text="Bot is running!")

    async def start():
        app = web.Application()
        app.router.add_get("/", handler)
        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.environ.get("PORT", 8080))
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start())
    loop.run_forever()

# ---------------- MAIN ---------------- #
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.run()
