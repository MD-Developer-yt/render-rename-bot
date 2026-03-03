import os
import time
import threading
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *

# ---------------- BOT SETUP ---------------- #

bot = Client(
    "render-rename-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---------------- MEMORY STORAGE ---------------- #

USERS = set()
CAPTIONS = {}
THUMBNAILS = {}
METADATA = {}
META_ENABLED = {}

START_TIME = time.time()

# ---------------- START ---------------- #

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    USERS.add(message.from_user.id)
    await message.reply(f"👋 Welcome {message.from_user.first_name}!\n\nUse /help to see commands.")


# ---------------- HELP ---------------- #

@bot.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):

    text = """
📖 *User Commands*

/setcaption - Reply to text to set caption  
/removecaption  
/seecaption  

/setthumbnail - Reply to photo  
/removethumbnail  
/viewthumbnail  

/setmetadata - Reply to file  
/meta on  
/meta off  

Send any file to process.
"""

    await message.reply(text)


# ---------------- CAPTION ---------------- #

@bot.on_message(filters.command("setcaption") & filters.private)
async def set_caption(client, message):
    if not message.reply_to_message:
        return await message.reply("Reply to a text message to set caption.")
    CAPTIONS[message.from_user.id] = message.reply_to_message.text
    await message.reply("✅ Caption saved.")


@bot.on_message(filters.command("removecaption") & filters.private)
async def remove_caption(client, message):
    CAPTIONS.pop(message.from_user.id, None)
    await message.reply("❌ Caption removed.")


@bot.on_message(filters.command("seecaption") & filters.private)
async def see_caption(client, message):
    cap = CAPTIONS.get(message.from_user.id, "No caption set.")
    await message.reply(f"📌 Your Caption:\n\n{cap}")


# ---------------- THUMBNAIL ---------------- #

@bot.on_message(filters.command("setthumbnail") & filters.private)
async def set_thumb(client, message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply("Reply to a photo to set thumbnail.")
    file_id = message.reply_to_message.photo.file_id
    THUMBNAILS[message.from_user.id] = file_id
    await message.reply("✅ Thumbnail saved.")


@bot.on_message(filters.command("removethumbnail") & filters.private)
async def remove_thumb(client, message):
    THUMBNAILS.pop(message.from_user.id, None)
    await message.reply("❌ Thumbnail removed.")


@bot.on_message(filters.command("viewthumbnail") & filters.private)
async def view_thumb(client, message):
    thumb = THUMBNAILS.get(message.from_user.id)
    if not thumb:
        return await message.reply("No thumbnail set.")
    await client.send_photo(message.chat.id, thumb)


# ---------------- METADATA ---------------- #

@bot.on_message(filters.command("setmetadata") & filters.private)
async def set_metadata(client, message):
    if not message.reply_to_message:
        return await message.reply("Reply to file to set metadata name.")
    METADATA[message.from_user.id] = message.reply_to_message.document.file_name
    await message.reply("✅ Metadata saved.")


@bot.on_message(filters.command("meta") & filters.private)
async def meta_toggle(client, message):
    if "on" in message.text.lower():
        META_ENABLED[message.from_user.id] = True
        await message.reply("🟢 Metadata enabled.")
    elif "off" in message.text.lower():
        META_ENABLED[message.from_user.id] = False
        await message.reply("🔴 Metadata disabled.")


# ---------------- FILE HANDLER ---------------- #

@bot.on_message(filters.document | filters.video | filters.audio)
async def handle_file(client, message):

    user_id = message.from_user.id
    file_path = await message.download()

    caption = CAPTIONS.get(user_id, "")
    thumb = THUMBNAILS.get(user_id)

    await client.send_document(
        message.chat.id,
        file_path,
        caption=caption,
        thumb=thumb
    )

    os.remove(file_path)


# ---------------- OWNER COMMANDS ---------------- #

@bot.on_message(filters.command("users") & filters.private)
async def users_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        return
    await message.reply(f"👥 Total Users: {len(USERS)}")


@bot.on_message(filters.command("status") & filters.private)
async def status_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        return
    uptime = int(time.time() - START_TIME)
    await message.reply(f"⏳ Uptime: {uptime} seconds")


@bot.on_message(filters.command("ping") & filters.private)
async def ping_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        return
    await message.reply("🏓 Pong!")


@bot.on_message(filters.command("broadcast") & filters.private)
async def broadcast_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        return
    if not message.reply_to_message:
        return await message.reply("Reply to a message to broadcast.")

    for user in USERS:
        try:
            await message.reply_to_message.copy(user)
        except:
            pass

    await message.reply("✅ Broadcast completed.")


@bot.on_message(filters.command("restart") & filters.private)
async def restart_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        return
    await message.reply("♻ Restarting...")
    os._exit(0)


# ---------------- WEB SERVER ---------------- #

def run_web():
    async def handler(request):
        return web.Response(text="Bot is running!")

    async def start():
        app = web.Application()
        app.router.add_get("/", handler)

        port = int(os.environ.get("PORT", 8080))

        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()

    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start())
    loop.run_forever()


# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.run()
