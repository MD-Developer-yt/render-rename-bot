import os
import time
import math
import ast
import asyncio
import subprocess
import threading
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database as db

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = Client("render-rename-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB


# -------- HEX PROGRESS BAR --------
async def progress(current, total, message, start):
    now = time.time()
    diff = now - start
    if diff == 0:
        return

    percent = current * 100 / total
    speed = current / diff
    eta = int((total - current) / speed) if speed > 0 else 0

    filled = int(percent // 10)
    bar = "⬢" * filled + "⬡" * (10 - filled)

    text = (
        f"{bar}\n\n"
        f"{percent:.2f}%\n"
        f"{speed/1024/1024:.2f} MB/s\n"
        f"ETA: {eta//60:02d}:{eta%60:02d}"
    )

    try:
        await message.edit(text)
    except:
        pass


# -------- START --------
@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    db.add_user(message.from_user.id)
    await message.reply(
        "Send file to rename.\nUse /setcaption /setthumbnail /setmetadata /setmedia"
    )


# -------- COMMANDS --------
@bot.on_message(filters.command("setcaption") & filters.private)
async def set_caption(client, message):
    db.set_caption(message.from_user.id, " ".join(message.text.split()[1:]))
    await message.reply("Caption saved.")


@bot.on_message(filters.command("setthumbnail") & filters.private)
async def set_thumb(client, message):
    if message.reply_to_message and message.reply_to_message.photo:
        os.makedirs("thumbs", exist_ok=True)
        path = f"thumbs/{message.from_user.id}.jpg"
        await message.reply_to_message.download(path)
        db.set_thumb(message.from_user.id, path)
        await message.reply("Thumbnail saved.")


@bot.on_message(filters.command("setmetadata") & filters.private)
async def set_meta(client, message):
    text = " ".join(message.text.split()[1:])
    if "=" not in text:
        return await message.reply("Use key=value")
    key, value = text.split("=", 1)
    meta = ast.literal_eval(db.get_metadata(message.from_user.id))
    meta[key.strip()] = value.strip()
    db.set_metadata(message.from_user.id, str(meta))
    await message.reply("Metadata added.")


@bot.on_message(filters.command("meta") & filters.private)
async def toggle_meta(client, message):
    status = message.text.split()[1].lower() == "on"
    db.set_meta_status(message.from_user.id, status)
    await message.reply("Metadata " + ("enabled." if status else "disabled."))


@bot.on_message(filters.command("setmedia") & filters.private)
async def set_media(client, message):
    mode = message.text.split()[1].lower()
    if mode in ["video", "document", "audio"]:
        db.set_media(message.from_user.id, mode)
        await message.reply("Media set.")
    else:
        await message.reply("Use video/document/audio")


# -------- FILE HANDLER --------
@bot.on_message(filters.video | filters.document | filters.audio)
async def handle(client, message):
    media = message.video or message.document or message.audio

    if media.file_size > MAX_FILE_SIZE:
        return await message.reply("File exceeds 2GB.")

    uid = message.from_user.id
    status = await message.reply("Processing...")
    start = time.time()

    file_path = await message.download(progress=progress, progress_args=(status, start))
    new_path = "renamed_" + os.path.basename(file_path)
    os.rename(file_path, new_path)

    # ---- METADATA STREAM COPY (LOW RAM) ----
    if db.get_meta_status(uid):
        meta_dict = ast.literal_eval(db.get_metadata(uid))
        if meta_dict:
            output = "meta_" + new_path
            cmd = ["ffmpeg", "-y", "-i", new_path, "-map", "0", "-c", "copy"]
            for k, v in meta_dict.items():
                cmd += ["-metadata", f"{k}={v}"]
            cmd.append(output)
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.remove(new_path)
            new_path = output

    start = time.time()
    send_args = dict(
        chat_id=message.chat.id,
        caption=db.get_caption(uid),
        thumb=db.get_thumb(uid),
        progress=progress,
        progress_args=(status, start)
    )

    mode = db.get_media(uid)

    if mode == "video":
        send_args["video"] = new_path
        await client.send_video(**send_args)
    elif mode == "audio":
        send_args["audio"] = new_path
        await client.send_audio(**send_args)
    else:
        send_args["document"] = new_path
        await client.send_document(**send_args)

    os.remove(new_path)
    await status.delete()


if __name__ == "__main__":
    from web import run
    threading.Thread(target=run).start()
    bot.run()
