import os
import time
import subprocess
import threading
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database as db
from web import run  # Flask web server for Render

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH"))
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", 123456))  # Replace with your Telegram ID

bot = Client(
    "render-rename-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=50
)

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

# ---------------- Progress ----------------
progress_cache = {}
async def progress(current, total, message, start):
    now = time.time()
    if message.id in progress_cache and now - progress_cache[message.id] < 2:
        return
    progress_cache[message.id] = now
    diff = now - start
    percent = current * 100 / total
    speed = current / diff if diff > 0 else 0
    eta = int((total - current) / speed) if speed > 0 else 0
    filled = int(percent // 10)
    bar = "⬢" * filled + "⬡" * (10 - filled)
    text = f"{bar}\n\n📊 {percent:.1f}%\n🚀 {speed/1024/1024:.2f} MB/s\n⏳ ETA {eta//60:02d}:{eta%60:02d}"
    try:
        await message.edit(text)
    except:
        pass

# ---------------- Buttons ----------------
def start_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙ Help", callback_data="help"),
         InlineKeyboardButton("ℹ About", callback_data="about")],
        [InlineKeyboardButton("🏷 Metadata", callback_data="meta"),
         InlineKeyboardButton("📁 Set Media", callback_data="setmedia")],
        [InlineKeyboardButton("🖼 Set Thumbnail", callback_data="setthumb"),
         InlineKeyboardButton("✏ Set Caption", callback_data="setcaption")]
    ])

# ---------------- Start ----------------
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    db.add_user(message.from_user.id)
    await message.reply_photo(
        photo="https://graph.org/file/0e77ba48a8b7a3b09296f-362372bee0d84fd217.jpg",
        caption=f"👋 Hello {message.from_user.first_name}\nSend file up to 2GB to rename.",
        reply_markup=start_buttons()
    )

# ---------------- Callbacks ----------------
@bot.on_callback_query()
async def callbacks(client, query):
    uid = query.from_user.id
    data = query.data

    if data == "help":
        await query.message.edit_text(
            "**Bot Commands**\n\n"
            "/setcaption - Set caption\n"
            "/see_caption - View caption\n"
            "/del_caption - Delete caption\n"
            "/setthumbnail - Reply photo to set thumbnail\n"
            "/viewthumb - View thumbnail\n"
            "/delthumb - Delete thumbnail\n"
            "/setmedia - Select media\n"
            "/setmetadata - Set metadata\n"
            "/status - Bot stats\n"
            "/broadcast - Broadcast message (Owner only)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
        )
    elif data == "about":
        await query.message.edit_text(
            "**AU Render Rename Bot**\n\n"
            "• Rename files up to 2GB\n"
            "• Caption support\n"
            "• Thumbnail support\n"
            "• Metadata editor\n\n"
            "Channel: @Anime_UpdatesAU",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
        )
    elif data == "back":
        await query.message.edit_text(
            "👋 Welcome Back",
            reply_markup=start_buttons()
        )
    elif data == "meta":
        status = db.get_metadata_status(uid)
        await query.message.edit_text(
            f"Metadata is {'✅ ON' if status else '❌ OFF'}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ON", callback_data="meta_on"),
                 InlineKeyboardButton("OFF", callback_data="meta_off")],
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ])
        )
    elif data == "meta_on":
        db.set_metadata_status(uid, True)
        await query.answer("Metadata Enabled")
    elif data == "meta_off":
        db.set_metadata_status(uid, False)
        await query.answer("Metadata Disabled")
    elif data == "setmedia":
        await query.message.edit_text(
            "Select Upload Mode:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎥 Video", callback_data="media_video"),
                 InlineKeyboardButton("📁 File", callback_data="media_document"),
                 InlineKeyboardButton("🎵 Audio", callback_data="media_audio")],
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ])
        )
    elif data.startswith("media_"):
        mode = data.split("_")[1]
        db.set_media(uid, mode)
        await query.answer(f"Media set to {mode}")
        await query.message.edit_text(f"✅ Media Mode set to **{mode}**")
    elif data == "setthumb":
        await query.message.edit_text("Reply to a photo with /setthumbnail to save your thumbnail.")
    elif data == "setcaption":
        await query.message.edit_text("Send /setcaption <text> to save caption.")

# ---------------- Caption Commands ----------------
@bot.on_message(filters.command("setcaption") & filters.private)
async def set_caption_cmd(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply("Send caption text.")
    db.set_caption(message.from_user.id, parts[1])
    await message.reply("✅ Caption saved.")

@bot.on_message(filters.command("see_caption") & filters.private)
async def see_caption_cmd(client, message):
    caption = db.get_caption(message.from_user.id)
    await message.reply(f"Current Caption:\n{caption if caption else 'None'}")

@bot.on_message(filters.command("del_caption") & filters.private)
async def del_caption_cmd(client, message):
    db.delete_caption(message.from_user.id)
    await message.reply("✅ Caption deleted.")

# ---------------- Thumbnail Commands ----------------
@bot.on_message(filters.command("setthumbnail") & filters.private)
async def set_thumbnail_cmd(client, message):
    if message.reply_to_message and message.reply_to_message.photo:
        os.makedirs("thumbs", exist_ok=True)
        path = f"thumbs/{message.from_user.id}.jpg"
        await message.reply_to_message.download(path)
        db.set_thumb(message.from_user.id, path)
        await message.reply("✅ Thumbnail saved.")
    else:
        await message.reply("Reply to a photo to set thumbnail.")

@bot.on_message(filters.command("viewthumb") & filters.private)
async def view_thumb_cmd(client, message):
    thumb = db.get_thumb(message.from_user.id)
    if thumb and os.path.exists(thumb):
        await message.reply_photo(thumb, caption="Current Thumbnail")
    else:
        await message.reply("No thumbnail set.")

@bot.on_message(filters.command("delthumb") & filters.private)
async def del_thumb_cmd(client, message):
    thumb = db.get_thumb(message.from_user.id)
    if thumb and os.path.exists(thumb):
        os.remove(thumb)
    db.delete_thumb(message.from_user.id)
    await message.reply("✅ Thumbnail deleted.")

# ---------------- Metadata Commands ----------------
@bot.on_message(filters.command("setmetadata") & filters.private)
async def set_metadata_cmd(client, message):
    metadata = {
        "title": "@Anime_UpdatesAU",
        "author": "@Anime_UpdatesAU",
        "artist": "@Anime_UpdatesAU",
        "audio": "@Anime_UpdatesAU",
        "video": "@Anime_UpdatesAU",
        "subtitle": "@Anime_UpdatesAU"
    }
    db.set_metadata(message.from_user.id, metadata)
    await message.reply(
        "✅ Metadata Set Successfully\n"
        "Title : @Anime_UpdatesAU\n"
        "Author : @Anime_UpdatesAU\n"
        "Artist : @Anime_UpdatesAU\n"
        "Audio : @Anime_UpdatesAU\n"
        "Video : @Anime_UpdatesAU\n"
        "Subtitle : @Anime_UpdatesAU"
    )

# ---------------- File Rename ----------------
@bot.on_message(filters.document | filters.video | filters.audio)
async def rename_file(client, message):
    media = message.document or message.video or message.audio
    if media.file_size > MAX_FILE_SIZE:
        return await message.reply("File exceeds 2GB.")
    uid = message.from_user.id
    caption = db.get_caption(uid)
    thumb = db.get_thumb(uid)
    mode = db.get_media(uid)
    meta = db.get_metadata(uid)
    path = await message.download()
    new_name = "AU_" + media.file_name
    output = new_name

    if meta:
        output = "meta_" + new_name
        cmd = [
            "ffmpeg","-y","-i",path,"-map","0","-c","copy"
        ]
        for k,v in meta.items():
            cmd += ["-metadata", f"{k}={v}"]
        cmd.append(output)
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(path)
    else:
        output = new_name

    send_args = {
        "chat_id": message.chat.id,
        "caption": caption,
        "thumb": thumb,
    }
    if mode == "video":
        send_args["video"] = output
        await client.send_video(**send_args)
    elif mode == "audio":
        send_args["audio"] = output
        await client.send_audio(**send_args)
    else:
        send_args["document"] = output
        await client.send_document(**send_args)

    os.remove(output)

# ---------------- Status ----------------
@bot.on_message(filters.command("status") & filters.user(OWNER_ID))
async def status_cmd(client, message):
    users = db.total_users()
    await message.reply(f"📊 Bot Status\nUsers: {users}")

# ---------------- Broadcast ----------------
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
    await message.reply(f"✅ Broadcast Done\nSuccess: {success}\nFailed: {fail}")

# ---------------- RUN ----------------
if __name__ == "__main__":
    threading.Thread(target=run).start()  # Start Flask web server
    print("Bot Started...")
    bot.run()
