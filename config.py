import os

# Telegram API credentials
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Channel username WITHOUT @
FORCE_JOIN = os.environ.get("FORCE_JOIN")

# Your Telegram User ID
OWNER_ID = int(os.environ.get("OWNER_ID", 0))

# Web Port (Render auto sets this)
PORT = int(os.environ.get("PORT", 8080))
