import os
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

# ---------------- FORCE JOIN ---------------- #

async def force_join(client, message):

    if message.from_user.id == OWNER_ID:
        return True

    if not FORCE_JOIN:
        return True

    try:
        member = await client.get_chat_member(FORCE_JOIN, message.from_user.id)

        if member.status in ["left", "kicked"]:
            await message.reply(
                f"🚫 Please join @{FORCE_JOIN} first to use this bot."
            )
            return False

        return True

    except:
        return True


# ---------------- START COMMAND ---------------- #

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):

    if not await force_join(client, message):
        return

    welcome_text = f"""
👋 Hello {message.from_user.first_name}!

✨ Welcome to RENDER RENAME BOT

📂 Send me any video, audio or document.
⚡ I will rename and resend it instantly.

🔒 Fast | Simple | Stable
"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Updates", url=f"https://t.me/{FORCE_JOIN}")
        ],
        [
            InlineKeyboardButton("👤 Owner", url=f"https://t.me/{message.from_user.username}" if message.from_user.username else "https://t.me")
        ]
    ])

    await message.reply_text(welcome_text, reply_markup=keyboard)


# ---------------- FILE HANDLER ---------------- #

@bot.on_message(filters.document | filters.video | filters.audio)
async def handle_file(client, message):

    if not await force_join(client, message):
        return

    msg = await message.reply("📥 Downloading...")
    file_path = await message.download()

    await message.reply("📤 Uploading...")

    await client.send_document(
        message.chat.id,
        file_path,
        caption="✨ Encoded by @Anime_UpdatesAU"
    )

    os.remove(file_path)
    await msg.delete()


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

        print(f"Web server started on port {port}")

    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start())
    loop.run_forever()


# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    print("Starting Web Server...")
    threading.Thread(target=run_web).start()

    print("Starting Telegram Bot...")
    bot.run()
