import os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

FORCE_JOIN = os.getenv("FORCE_JOIN", "Anime_UpdatesAU")  # channel username without @
PORT = int(os.getenv("PORT", 8080))
