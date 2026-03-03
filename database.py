# database.py
import sqlite3
import os

# Create folder if needed
os.makedirs("thumbnails", exist_ok=True)

# Connect to SQLite database
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

# Create users table
cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    caption TEXT,
    thumb TEXT,
    media TEXT DEFAULT 'document'
)
""")
conn.commit()

# ---------------- USER FUNCTIONS ---------------- #

def add_user(user_id: int):
    """Add new user if not exists"""
    cur.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
    conn.commit()

# ---------------- CAPTION ---------------- #

def set_caption(user_id: int, text: str):
    cur.execute("UPDATE users SET caption=? WHERE user_id=?", (text, user_id))
    conn.commit()

def get_caption(user_id: int):
    cur.execute("SELECT caption FROM users WHERE user_id=?", (user_id,))
    data = cur.fetchone()
    return data[0] if data and data[0] else None

# ---------------- THUMBNAIL ---------------- #

def set_thumb(user_id: int, path: str):
    cur.execute("UPDATE users SET thumb=? WHERE user_id=?", (path, user_id))
    conn.commit()

def get_thumb(user_id: int):
    cur.execute("SELECT thumb FROM users WHERE user_id=?", (user_id,))
    data = cur.fetchone()
    return data[0] if data and data[0] else None

# ---------------- MEDIA TYPE ---------------- #

def set_media(user_id: int, media_type: str):
    """media_type can be 'video', 'audio', or 'document'"""
    cur.execute("UPDATE users SET media=? WHERE user_id=?", (media_type, user_id))
    conn.commit()

def get_media(user_id: int):
    cur.execute("SELECT media FROM users WHERE user_id=?", (user_id,))
    data = cur.fetchone()
    return data[0] if data and data[0] else "document"
