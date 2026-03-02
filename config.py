import os

API_ID = int(os.getenv("API_ID", "123456"))
API_HASH = os.getenv("API_HASH", "your_api_hash")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")

FORCE_JOIN = os.getenv("FORCE_JOIN", "Anime_UpdatesAU")  # without @

PORT = int(os.getenv("PORT", 8080))
