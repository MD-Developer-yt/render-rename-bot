import asyncio
import os
import time
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *

# Python 3.14 loop fix
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

os.makedirs("downloads", exist_ok=True)

METADATA_TEXT = """
Title : @Anime_UpdatesAU
Encoded by : @Anime_UpdatesAU
"""

bot = Client(
    "render-rename-bot",
    api_id=int(API_ID),
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---------------- FORCE JOIN WITH OWNER BYPASS ---------------- #

async def force_join(client, message):

    if message.from_user.id == OWNER_ID:
        return True

    if not FORCE_JOIN:
        return True

    try:
        member = await client.get_chat_member(FORCE_JOIN, message.from_user.id)
        if member.status in ["left", "kicked"]:
            await message.reply(f"Join @{FORCE_JOIN} first")
            return False
        return True
    except:
        await message.reply(f"Join @{FORCE_JOIN} first")
        return False


# ---------------- START COMMAND ---------------- #

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):

    if not await force_join(client, message):
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("METADATA", callback_data="meta")]
    ])

    await message.reply("RENDER RENAME BOT WORKING", reply_markup=keyboard)


# ---------------- RENAME ---------------- #

@bot.on_message(filters.document | filters.video | filters.audio)
async def rename_file(client, message):

    if not await force_join(client, message):
        return

    msg = await message.reply("Downloading...")
    file_path = await message.download(file_name=f"downloads/{message.id}")

    await message.reply("Uploading...")

    await client.send_document(
        message.chat.id,
        file_path,
        caption=METADATA_TEXT
    )

    os.remove(file_path)
    await msg.delete()


# ---------------- WEB SERVER (PORT 8080) ---------------- #

async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web():
    app = web.Application()
    app.router.add_get("/", handle)

    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server started on port {port}")


# ---------------- MAIN ---------------- #

async def main():
    await bot.start()
    print("Telegram Bot Started")
    await start_web()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
