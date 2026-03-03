import os
import asyncio
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

# ---------------- FORCE JOIN ---------------- #

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

    except Exception as e:
        print("Force Join Error:", e)
        return True


# ---------------- START COMMAND ---------------- #

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):

    if not await force_join(client, message):
        return

    await message.reply("✅ Bot is working properly")


# ---------------- FILE HANDLER ---------------- #

@bot.on_message(filters.document | filters.video | filters.audio)
async def handle_file(client, message):

    if not await force_join(client, message):
        return

    msg = await message.reply("Downloading...")
    file_path = await message.download()

    await message.reply("Uploading...")

    await client.send_document(
        message.chat.id,
        file_path,
        caption="Encoded by @Anime_UpdatesAU"
    )

    os.remove(file_path)
    await msg.delete()


# ---------------- WEB SERVER ---------------- #

async def web_handler(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", web_handler)

    port = int(os.environ.get("PORT", 8080))

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print(f"Web server started on port {port}")


# ---------------- START EVERYTHING ---------------- #

async def main():
    await bot.start()
    print("Telegram Bot Started")
    await start_web_server()
    await asyncio.Event().wait()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
