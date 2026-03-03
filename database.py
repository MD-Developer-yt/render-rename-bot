import sqlite3
import os

# Create database folder if not exists
os.makedirs("data", exist_ok=True)
conn = sqlite3.connect("data/bot.db", check_same_thread=False)
cur = conn.cursor()

# ---------------- TABLE ---------------- #
cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    caption TEXT,
    thumb TEXT,
    media TEXT DEFAULT 'document'
)
""")
conn.commit()

# ---------------- USER ---------------- #
def add_user(user_id):
    cur.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
    conn.commit()

# ---------------- CAPTION ---------------- #
def set_caption(user_id, caption):
    cur.execute("UPDATE users SET caption=? WHERE user_id=?", (caption, user_id))
    conn.commit()

def get_caption(user_id):
    cur.execute("SELECT caption FROM users WHERE user_id=?", (user_id,))
    res = cur.fetchone()
    return res[0] if res and res[0] else None

# ---------------- THUMBNAIL ---------------- #
def set_thumb(user_id, path):
    cur.execute("UPDATE users SET thumb=? WHERE user_id=?", (path, user_id))
    conn.commit()

def get_thumb(user_id):
    cur.execute("SELECT thumb FROM users WHERE user_id=?", (user_id,))
    res = cur.fetchone()
    return res[0] if res and res[0] else None

# ---------------- MEDIA ---------------- #
def set_media(user_id, media_type):
    cur.execute("UPDATE users SET media=? WHERE user_id=?", (media_type, user_id))
    conn.commit()

def get_media(user_id):
    cur.execute("SELECT media FROM users WHERE user_id=?", (user_id,))
    res = cur.fetchone()
    return res[0] if res else "document"
