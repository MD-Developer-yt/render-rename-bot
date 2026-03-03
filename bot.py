import os, time, asyncio, threading, subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import *
from config import *

# ---------------- DIRECTORIES ---------------- #
os.makedirs("downloads", exist_ok=True)
os.makedirs("thumbnails", exist_ok=True)

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB limit

# ---------------- BOT ---------------- #
bot = Client(
    "rename-render-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---------------- PROGRESS BAR ---------------- #
async def progress(current, total, msg, start, action="Processing"):
    now = time.time()
    diff = now - start
    if diff == 0:
        return
    percent = current * 100 / total
    speed = current / diff
    eta = round((total - current) / speed) if speed > 0 else 0
    bar = "█" * int(percent / 5) + "░" * (20 - int(percent / 5))
    try:
        await msg.edit(f"{action}\n[{bar}] {percent:.2f}%\nSpeed: {speed/1024/1024:.2f} MB/s\nETA: {eta}s")
    except:
        pass

# ---------------- START ---------------- #
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    add_user(message.from_user.id)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📯 Anime Updates", url="https://t.me/Anime_UpdatesAU"),
         InlineKeyboardButton("💬 Support", url="https://t.me/AU_Bot_Discussion")],
        [InlineKeyboardButton("🎛️ About", callback_data="about"),
         InlineKeyboardButton("🛠 Help", callback_data="help")]
    ])
    text = f"👋 Hello {message.from_user.first_name}!\n\nWelcome to 2GB Rename Bot.\nSend any file (Video/Audio/Document) to rename it."
    photo = "https://graph.org/file/0e77ba48a8b7a3b09296f-362372bee0d84fd217.jpg"
    await message.reply_photo(photo=photo, caption=text, reply_markup=kb)

# ---------------- CALLBACKS ---------------- #
@bot.on_callback_query(filters.regex("help"))
async def help_cb(c, q):
    txt = (
        "📖 Commands:\n\n"
        "/setcaption - Set caption\n"
        "/removecaption - Remove caption\n"
        "/seecaption - See saved caption\n"
        "/setthumbnail - Set thumbnail\n"
        "/removethumbnail - Remove thumbnail\n"
        "/viewthumbnail - View thumbnail\n"
        "/setmetadata - Set metadata (Title, Author, Artist, Video, Audio, Subtitle, Encoded by)\n"
        "/setmedia - Set media type (video/audio/document)\n"
        "/meta on/off - Enable/Disable metadata\n"
        "/restart - Restart bot\n"
        "/status - Bot status\n"
        "/users - Total users\n"
        "/broadcast - Send message to all users\n"
        "/ping - Check bot speed\n"
        "/info - Bot info\n"
    )
    await q.message.edit(txt)

@bot.on_callback_query(filters.regex("about"))
async def about_cb(c, q):
    txt = (
        "🤖 Bot Name: 2GB Rename Bot\n"
        "👨‍💻 Developer: @Mr_Mohammed_29\n"
        "📚 Features: Rename files, add caption, thumbnail, metadata, 2GB support, progress bar\n"
    )
    await q.message.edit(txt)

# ---------------- SET CAPTION ---------------- #
@bot.on_message(filters.command("setcaption") & filters.private)
async def set_caption_cmd(c, m):
    await m.reply("Send me the caption text:")
    @bot.on_message(filters.text & filters.private)
    async def save_caption(c2, m2):
        set_caption(m2.from_user.id, m2.text)
        await m2.reply("✅ Caption saved.")

@bot.on_message(filters.command("seecaption") & filters.private)
async def see_caption(c, m):
    cap = get_caption(m.from_user.id)
    await m.reply(f"📄 Saved Caption:\n{cap if cap else 'No caption set.'}")

@bot.on_message(filters.command("removecaption") & filters.private)
async def remove_caption(c, m):
    set_caption(m.from_user.id, None)
    await m.reply("🗑 Caption removed.")

# ---------------- SET THUMBNAIL ---------------- #
@bot.on_message(filters.command("setthumbnail") & filters.private)
async def set_thumb_cmd(c, m):
    await m.reply("Send photo for thumbnail:")
    @bot.on_message(filters.photo & filters.private)
    async def save_thumb(c2, m2):
        path = f"thumbnails/{m2.from_user.id}.jpg"
        await m2.download(path)
        set_thumb(m2.from_user.id, path)
        await m2.reply("✅ Thumbnail saved.")

@bot.on_message(filters.command("viewthumbnail") & filters.private)
async def view_thumb(c, m):
    thumb = get_thumb(m.from_user.id)
    if thumb:
        await m.reply_photo(thumb)
    else:
        await m.reply("No thumbnail set.")

@bot.on_message(filters.command("removethumbnail") & filters.private)
async def remove_thumb(c, m):
    set_thumb(m.from_user.id, None)
    await m.reply("🗑 Thumbnail removed.")

# ---------------- SET METADATA ---------------- #
@bot.on_message(filters.command("setmetadata") & filters.private)
async def set_metadata_cmd(c, m):
    await m.reply(
        "Send metadata in format:\nTitle=...\nAuthor=...\nArtist=...\nAudio=...\nVideo=...\nSubtitle=...\nEncoded_by=..."
    )

# ---------------- SET MEDIA ---------------- #
@bot.on_message(filters.command("setmedia") & filters.private)
async def set_media_cmd(c, m):
    args = m.text.split()
    if len(args) < 2:
        return await m.reply("Usage: /setmedia video|audio|document")
    mode = args[1].lower()
    if mode not in ["video","audio","document"]:
        return await m.reply("Choose video/audio/document")
    set_media(m.from_user.id, mode)
    await m.reply(f"✅ Media mode set to {mode}")

# ---------------- FILE HANDLER ---------------- #
@bot.on_message(filters.document | filters.video | filters.audio)
async def handle_file(c, m):
    uid = m.from_user.id
    add_user(uid)
    file = m.document or m.video or m.audio

    if file.file_size > MAX_FILE_SIZE:
        return await m.reply("❌ File exceeds 2GB limit")

    msg = await m.reply("📥 Downloading...")
    start = time.time()
    file_path = await m.download(f"downloads/{m.message_id}", progress=progress, progress_args=(msg, start, "📥 Downloading..."))

    media_mode = get_media(uid)
    caption = get_caption(uid)
    thumb = get_thumb(uid)

    upload_msg = await m.reply("📤 Uploading...")
    start2 = time.time()

    if media_mode=="video":
        await c.send_video(m.chat.id, file_path, caption=caption, thumb=thumb, progress=progress, progress_args=(upload_msg, start2, "📤 Uploading..."))
    elif media_mode=="audio":
        await c.send_audio(m.chat.id, file_path, caption=caption, thumb=thumb, progress=progress, progress_args=(upload_msg, start2, "📤 Uploading..."))
    else:
        await c.send_document(m.chat.id, file_path, caption=caption, thumb=thumb, progress=progress, progress_args=(upload_msg, start2, "📤 Uploading..."))

    os.remove(file_path)
    await msg.delete()
    await upload_msg.delete()

# ---------------- WEB SERVER (Render Free Plan) ---------------- #
def run_web():
    from aiohttp import web

    async def handler(req):
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
if __name__=="__main__":
    threading.Thread(target=run_web).start()
    bot.run()
