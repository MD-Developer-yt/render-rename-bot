import sqlite3
import os
import json

DB_NAME = "bot.db"

# ---------------- INIT ----------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            caption TEXT,
            thumb TEXT,
            media TEXT DEFAULT 'document',
            metadata TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- USERS ----------------
def add_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def total_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count

# ---------------- CAPTION ----------------
def set_caption(user_id, text):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET caption=? WHERE id=?", (text, user_id))
    conn.commit()
    conn.close()

def get_caption(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT caption FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def delete_caption(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET caption=NULL WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

# ---------------- THUMBNAIL ----------------
def set_thumb(user_id, path):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET thumb=? WHERE id=?", (path, user_id))
    conn.commit()
    conn.close()

def get_thumb(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT thumb FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def delete_thumb(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET thumb=NULL WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

# ---------------- MEDIA ----------------
def set_media(user_id, mode):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET media=? WHERE id=?", (mode, user_id))
    conn.commit()
    conn.close()

def get_media(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT media FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else "document"

# ---------------- METADATA ----------------
def set_metadata(user_id, metadata: dict):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    metadata_json = json.dumps(metadata)
    c.execute("UPDATE users SET metadata=? WHERE id=?", (metadata_json, user_id))
    conn.commit()
    conn.close()

def get_metadata(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT metadata FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        return json.loads(row[0])
    return None

def get_metadata_status(user_id):
    return get_metadata(user_id) is not None

def set_metadata_status(user_id, status: bool):
    if not status:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE users SET metadata=NULL WHERE id=?", (user_id,))
        conn.commit()
        conn.close()
    else:
        # default metadata
        set_metadata(user_id, {
            "title": "@Anime_UpdatesAU",
            "author": "@Anime_UpdatesAU",
            "artist": "@Anime_UpdatesAU",
            "audio": "@Anime_UpdatesAU",
            "video": "@Anime_UpdatesAU",
            "subtitle": "@Anime_UpdatesAU"
        })
