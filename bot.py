import os, time, asyncio, threading, subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import *
from config import *

# ---------------- BOT ---------------- #
bot = Client("rename-render-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

PROGRESS_BAR = """\n
<b>🔗 Size :</b> {1} | {2}
<b>⏳️ Done :</b> {0}%
<b>🚀 Speed :</b> {3}/s
<b>⏰️ ETA :</b> {4}
"""

# ---------------- PROGRESS ---------------- #
async def progress(current, total, msg, start_time, action=""):
    now = time.time()
    diff = now - start_time
    if diff == 0:
        return
    percentage = current * 100 / total
    speed = current / diff
    eta = round((total - current) / speed) if speed > 0 else 0
    try:
        await msg.edit(PROGRESS_BAR.format(round(percentage, 2),
                                           round(current/1024/1024,2),
                                           round(total/1024/1024,2),
                                           round(speed/1024/1024,2),
                                           eta))
    except:
        pass

# ---------------- START ---------------- #
@bot.on_message(filters.private & filters.command("start"))
async def start_cmd(client, message):
    add_user(message.from_user.id)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Home", callback_data="start"),
         InlineKeyboardButton("ℹ️ About", callback_data="about")],
        [InlineKeyboardButton("💬 Help", callback_data="help")]
    ])
    await message.reply_text(f"👋 Hello {message.from_user.first_name}!\nWelcome to 2GB Rename Bot.", reply_markup=kb)

# ---------------- CALLBACK ---------------- #
@bot.on_callback_query()
async def cb(client, query):
    data = query.data
    if data == "start":
        await query.message.edit_text("🏠 Home Screen", reply_markup=query.message.reply_markup)
    elif data == "help":
        await query.message.edit_text(
            "/setcaption\n/removecaption\n/seecaption\n"
            "/setthumbnail\n/removethumbnail\n/viewthumbnail\n"
            "/setmetadata\n/meta on/off\n/setmedia video|document|audio\n",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="start")]])
        )
    elif data == "about":
        await query.message.edit_text(f"🤖 2GB Rename Bot\nDeveloper: {OWNER_ID}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="start")]]))

# ---------------- FILE HANDLER ---------------- #
@bot.on_message(filters.document | filters.video | filters.audio)
async def rename_file(client, message):
    add_user(message.from_user.id)
    media = message.video or message.document or message.audio
    if media.file_size > MAX_FILE_SIZE:
        return await message.reply("❌ File exceeds 2GB limit")
    msg = await message.reply("📥 Downloading...")
    start_time = time.time()
    file_path = await message.download(file_name=f"{message.from_user.id}_{int(time.time())}", progress=progress, progress_args=(msg, start_time, "Downloading"))
    # Apply metadata if exists
    metadata = get_metadata(message.from_user.id)
    if metadata:
        await msg.edit("🛠 Applying metadata...")
        out_path = file_path + "_meta.mp4"
        cmd = ["ffmpeg","-y","-i",file_path]
        for key, value in (eval(metadata) if isinstance(metadata,str) else metadata).items():
            cmd += ["-metadata", f"{key}={value}"]
        cmd += ["-codec","copy", out_path]
        subprocess.run(cmd)
        os.remove(file_path)
        file_path = out_path
    await msg.edit("📤 Uploading...")
    mode = get_media(message.from_user.id) or "document"
    if mode == "video":
        await client.send_video(message.chat.id, file_path)
    elif mode == "audio":
        await client.send_audio(message.chat.id, file_path)
    else:
        await client.send_document(message.chat.id, file_path)
    os.remove(file_path)
    await msg.delete()

# ---------------- WEB SERVER (Render) ---------------- #
def run_web():
    from aiohttp import web
    async def handler(request):
        return web.Response(text="Bot is running!")
    async def start():
        app = web.Application()
        app.router.add_get("/", handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", PORT)
        await site.start()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start())
    loop.run_forever()

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.run()
