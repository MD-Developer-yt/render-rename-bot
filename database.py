import sqlite3
import os
import json

DB_PATH = "botdata.db"

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# ---------------- CREATE TABLES ---------------- #
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    caption TEXT,
    thumb TEXT,
    media TEXT DEFAULT 'document',
    metadata TEXT
)
""")
conn.commit()

# ---------------- USERS ---------------- #
def add_user(user_id: int):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

def get_users():
    cursor.execute("SELECT user_id FROM users")
    return [row[0] for row in cursor.fetchall()]

def total_users():
    cursor.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0]

# ---------------- CAPTION ---------------- #
def set_caption(user_id: int, caption: str):
    cursor.execute("UPDATE users SET caption = ? WHERE user_id = ?", (caption, user_id))
    conn.commit()

def get_caption(user_id: int):
    cursor.execute("SELECT caption FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row and row[0] else ""

# ---------------- THUMBNAIL ---------------- #
def set_thumb(user_id: int, path: str):
    cursor.execute("UPDATE users SET thumb = ? WHERE user_id = ?", (path, user_id))
    conn.commit()

def get_thumb(user_id: int):
    cursor.execute("SELECT thumb FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row and row[0] else None

# ---------------- MEDIA ---------------- #
def set_media(user_id: int, media_type: str):
    cursor.execute("UPDATE users SET media = ? WHERE user_id = ?", (media_type, user_id))
    conn.commit()

def get_media(user_id: int):
    cursor.execute("SELECT media FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row and row[0] else "document"

# ---------------- METADATA ---------------- #
def set_metadata(user_id: int, metadata: dict):
    metadata_json = json.dumps(metadata)
    cursor.execute("UPDATE users SET metadata = ? WHERE user_id = ?", (metadata_json, user_id))
    conn.commit()

def get_metadata(user_id: int):
    cursor.execute("SELECT metadata FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row and row[0]:
        return json.loads(row[0])
    return None
