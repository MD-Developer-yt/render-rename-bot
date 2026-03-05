import os
import subprocess
import time
import threading
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database as db
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID

bot = Client("render-rename-bot",
             api_id=API_ID,
             api_hash=API_HASH,
             bot_token=BOT_TOKEN)

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

# ---------------- START BUTTONS ---------------- #
def start_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙ Help", callback_data="help")],
        [InlineKeyboardButton("ℹ About", callback_data="about")],
        [InlineKeyboardButton("🏷 Metadata", callback_data="meta")]
    ])

# ---------------- START ---------------- #
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    db.add_user(message.from_user.id)
    await message.reply_text("👋 Hᴇʟʟᴏ {message.from_user.first_name}!\n"
                             "🤖 Wᴇʟᴄᴏᴍᴇ Tᴏ AU Rᴇɴᴅᴇʀ Rᴇɴᴀᴍᴇ Bᴏᴛ\n\n"
                             "• Tʜɪs Is Aɴ Aᴅᴠᴀɴᴄᴇᴅ Aɴᴅ Yᴇᴛ Pᴏᴡᴇʀꜰᴜʟ ɪʟʟᴇɢᴀʟ Rᴇɴᴀᴍᴇ Bᴏᴛ.\n"
                             "• Usɪɴɢ Tʜɪs Bᴏᴛ Yᴏᴜ Cᴀɴ Rᴇɴᴀᴍᴇ & Cʜᴀɴɢᴇ Tʜᴜᴍʙɴᴀɪʟ Oꜰ Yᴏᴜʀ Fɪʟᴇ.\n"
                             "• Yᴏᴜ Cᴀɴ Aʟsᴏ Cᴏɴᴠᴇʀᴛ Vɪᴅᴇᴏ Tᴏ Fɪʟᴇ & Fɪʟᴇ Tᴏ Vɪᴅᴇᴏ.\n\n"
                             "Tʜɪs Bᴏᴛ Wᴀs Cʀᴇᴀᴛᴇᴅ Bʏ :@Mr_Mohammed_29\n.", reply_markup=start_buttons())

# ---------------- CALLBACKS ---------------- #
@bot.on_callback_query()
async def callbacks(client, query):
    uid = query.from_user.id
    data = query.data

    # BACK
    if data == "home":
        await query.message.edit_text("👋 Hᴇʟʟᴏ {message.from_user.first_name}!\n"
                                      "🤖 Wᴇʟᴄᴏᴍᴇ Tᴏ AU Rᴇɴᴅᴇʀ Rᴇɴᴀᴍᴇ Bᴏᴛ\n\n"
                                      "• Tʜɪs Is Aɴ Aᴅᴠᴀɴᴄᴇᴅ Aɴᴅ Yᴇᴛ Pᴏᴡᴇʀꜰᴜʟ ɪʟʟᴇɢᴀʟ Rᴇɴᴀᴍᴇ Bᴏᴛ.\n"
                                      "• Usɪɴɢ Tʜɪs Bᴏᴛ Yᴏᴜ Cᴀɴ Rᴇɴᴀᴍᴇ & Cʜᴀɴɢᴇ Tʜᴜᴍʙɴᴀɪʟ Oꜰ Yᴏᴜʀ Fɪʟᴇ.\n"
                                      "• Yᴏᴜ Cᴀɴ Aʟsᴏ Cᴏɴᴠᴇʀᴛ Vɪᴅᴇᴏ Tᴏ Fɪʟᴇ & Fɪʟᴇ Tᴏ Vɪᴅᴇᴏ.\n\n"
                                      "ʜɪs Bᴏᴛ Wᴀs Cʀᴇᴀᴛᴇᴅ Bʏ :@Mr_Mohammed_29\n", reply_markup=start_buttons())

    # HELP
    elif data == "help":
        await query.message.edit_text(
            "**Bot Commands**\n"
            "/setmedia - Select upload type\n"
            "/setmetadata - Set metadata\n"
            "/status - Bot stats\n"
            "/broadcast - Admin broadcast\n"
            "/viewthumb - View your thumbnail\n"
            "/delthumb - Delete thumbnail\n"
            "/setcaption - Set caption\n"
            "/see_caption - View caption\n"
            "/del_caption - Delete caption\n"
            "/ping - Check bot ping\n"
            "/set_prefix / see_prefix / del_prefix\n"
            "/set_suffix / see_suffix / del_suffix",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="home")]])
        )

    # ABOUT
    elif data == "about":
        await query.message.edit_text(
            "🤖 Bot: **AU Render Rename Bot**\n"
            "📕 Library : Pyrogram\n"
            "✏️ Language : Python 3\n"
            "💾 Database : Mongo DB\n"
            "👨‍💻 Developer : @Mr_Mohammed_29\n"
            "📢 Updates : @Anime_UpdatesAU\n"
            "💬 Support : @AU_Bot_Discussion\n"
            "📊 Build Version : @BotsServerDead",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="home")]])
        )

    # MEDIA SELECT
    elif data.startswith("media_"):
        mode = data.split("_")[1]
        db.set_media(uid, mode)
        await query.answer(f"Media set to {mode}")
        await query.message.edit_text(f"✅ Media Mode: {mode}")

    # METADATA
    elif data == "meta":
        status = db.get_metadata_status(uid)
        await query.message.edit_text(
            f"Metadata is {'✅ ON' if status else '❌ OFF'}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ON", callback_data="meta_on"),
                 InlineKeyboardButton("OFF", callback_data="meta_off")],
                [InlineKeyboardButton("🔙 Back", callback_data="home")]
            ])
        )
    elif data == "meta_on":
        db.set_metadata_status(uid, True)
        await query.answer("Metadata Enabled")
    elif data == "meta_off":
        db.set_metadata_status(uid, False)
        await query.answer("Metadata Disabled")

# ---------------- SET MEDIA ---------------- #
@bot.on_message(filters.command("setmedia") & filters.private)
async def set_media(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎥 Video", callback_data="media_video"),
         InlineKeyboardButton("📁 File", callback_data="media_document"),
         InlineKeyboardButton("🎵 Audio", callback_data="media_audio")]
    ])
    await message.reply_text("Select upload mode:", reply_markup=buttons)

# ---------------- SET METADATA ---------------- #
@bot.on_message(filters.command("setmetadata") & filters.private)
async def set_metadata(client, message):
    metadata = {
        "title": "@Anime_UpdatesAU",
        "author": "@Anime_UpdatesAU",
        "artist": "@Anime_UpdatesAU",
        "audio": "@Anime_UpdatesAU",
        "video": "@Anime_UpdatesAU",
        "subtitle": "@Anime_UpdatesAU"
    }
    db.set_metadata(message.from_user.id, metadata)
    await message.reply_text(
        "✅ Metadata Set\n"
        "Title : @Anime_UpdatesAU\n"
        "Author : @Anime_UpdatesAU\n"
        "Artist : @Anime_UpdatesAU\n"
        "Audio : @Anime_UpdatesAU\n"
        "Video : @Anime_UpdatesAU\n"
        "Subtitle : @Anime_UpdatesAU"
    )

# ---------------- THUMBNAIL ---------------- #
@bot.on_message(filters.command("viewthumb") & filters.private)
async def view_thumb(client, message):
    thumb = db.get_thumb(message.from_user.id)
    if thumb and os.path.exists(thumb):
        await message.reply_photo(thumb, caption="Your thumbnail")
    else:
        await message.reply("No thumbnail set.")

@bot.on_message(filters.command("delthumb") & filters.private)
async def del_thumb(client, message):
    thumb = db.get_thumb(message.from_user.id)
    if thumb and os.path.exists(thumb):
        os.remove(thumb)
    db.set_thumb(message.from_user.id, None)
    await message.reply("Thumbnail deleted.")

# ---------------- CAPTION ---------------- #
@bot.on_message(filters.command("setcaption") & filters.private)
async def set_caption(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply("Send caption text")
    db.set_caption(message.from_user.id, parts[1])
    await message.reply("✅ Caption saved")

@bot.on_message(filters.command("see_caption") & filters.private)
async def see_caption(client, message):
    cap = db.get_caption(message.from_user.id)
    await message.reply(f"Your caption: {cap}" if cap else "No caption set.")

@bot.on_message(filters.command("del_caption") & filters.private)
async def del_caption(client, message):
    db.set_caption(message.from_user.id, None)
    await message.reply("Caption deleted.")

# ---------------- PREFIX / SUFFIX ---------------- #
@bot.on_message(filters.command("set_prefix") & filters.private)
async def set_prefix(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts)<2: return await message.reply("Usage: /set_prefix <text>")
    db.set_prefix(message.from_user.id, parts[1])
    await message.reply("Prefix saved.")

@bot.on_message(filters.command("see_prefix") & filters.private)
async def see_prefix(client, message):
    prefix = db.get_prefix(message.from_user.id)
    await message.reply(f"Prefix: {prefix}" if prefix else "No prefix set.")

@bot.on_message(filters.command("del_prefix") & filters.private)
async def del_prefix(client, message):
    db.set_prefix(message.from_user.id, None)
    await message.reply("Prefix deleted.")

@bot.on_message(filters.command("set_suffix") & filters.private)
async def set_suffix(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts)<2: return await message.reply("Usage: /set_suffix <text>")
    db.set_suffix(message.from_user.id, parts[1])
    await message.reply("Suffix saved.")

@bot.on_message(filters.command("see_suffix") & filters.private)
async def see_suffix(client, message):
    suffix = db.get_suffix(message.from_user.id)
    await message.reply(f"Suffix: {suffix}" if suffix else "No suffix set.")

@bot.on_message(filters.command("del_suffix") & filters.private)
async def del_suffix(client, message):
    db.set_suffix(message.from_user.id, None)
    await message.reply("Suffix deleted.")

# ---------------- PING ---------------- #
@bot.on_message(filters.command("ping") & filters.private)
async def ping_cmd(client, message):
    start = time.time()
    msg = await message.reply("🏓 Pinging...")
    end = time.time()
    await msg.edit(f"🏓 Pong!\nPing: {round((end-start)*1000)} ms")

# ---------------- BROADCAST ---------------- #
@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(client, message):
    if not message.reply_to_message:
        return await message.reply("Reply to a message to broadcast")
    users = db.get_users()
    success = fail = 0
    for user in users:
        try:
            await message.reply_to_message.copy(user)
            success += 1
        except:
            fail += 1
    await message.reply(f"✅ Broadcast done\nSuccess: {success}\nFailed: {fail}")

# ---------------- STATUS ---------------- #
@bot.on_message(filters.command("status") & filters.user(OWNER_ID))
async def status_cmd(client, message):
    users = db.total_users()
    await message.reply(f"📊 Bot Status\nUsers: {users}")

# ---------------- FILE HANDLER ---------------- #
@bot.on_message(filters.document | filters.video | filters.audio)
async def file_handler(client, message):
    uid = message.from_user.id
    caption = db.get_caption(uid) or "Uploaded by @Anime_UpdatesAU"
    thumb = db.get_thumb(uid)
    mode = db.get_media(uid) or "document"
    meta = db.get_metadata_status(uid)
    prefix = db.get_prefix(uid) or ""
    suffix = db.get_suffix(uid) or ""

    path = await message.download()
    base_name = os.path.basename(path)
    new_name = f"{prefix}{base_name}{suffix}"

    if meta:
        output = "meta_" + new_name
        cmd = [
            "ffmpeg","-y","-i",path,"-map","0","-c","copy",
            "-metadata","title=@Anime_UpdatesAU",
            "-metadata","author=@Anime_UpdatesAU",
            "-metadata","artist=@Anime_UpdatesAU",
            "-metadata","audio=@Anime_UpdatesAU",
            "-metadata","video=@Anime_UpdatesAU",
            "-metadata","subtitle=@Anime_UpdatesAU",
            output
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(path)
        path = output
    else:
        path = path

    if mode == "video":
        await message.reply_video(path, caption=caption, thumb=thumb)
    elif mode == "audio":
        await message.reply_audio(path, caption=caption)
    else:
        await message.reply_document(path, caption=caption, thumb=thumb)

    os.remove(path)

# ---------------- RUN BOT ---------------- #
print("Bot Started...")
bot.run()
