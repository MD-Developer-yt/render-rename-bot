import sqlite3
import json
import os

DB_FILE = "botdata.db"

# Ensure DB exists
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# ---------------- CREATE TABLE ---------------- #
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    caption TEXT,
    thumb TEXT,
    media TEXT,
    metadata TEXT,
    prefix TEXT,
    suffix TEXT
)
""")
conn.commit()

# ---------------- USERS ---------------- #
def add_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
    conn.commit()

def get_users():
    cursor.execute("SELECT user_id FROM users")
    return [row[0] for row in cursor.fetchall()]

def total_users():
    cursor.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0]

# ---------------- CAPTION ---------------- #
def set_caption(user_id, caption):
    cursor.execute("UPDATE users SET caption=? WHERE user_id=?", (caption, user_id))
    conn.commit()

def get_caption(user_id):
    cursor.execute("SELECT caption FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else None

# ---------------- THUMBNAIL ---------------- #
def set_thumb(user_id, path):
    cursor.execute("UPDATE users SET thumb=? WHERE user_id=?", (path, user_id))
    conn.commit()

def get_thumb(user_id):
    cursor.execute("SELECT thumb FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else None

# ---------------- MEDIA ---------------- #
def set_media(user_id, media):
    cursor.execute("UPDATE users SET media=? WHERE user_id=?", (media, user_id))
    conn.commit()

def get_media(user_id):
    cursor.execute("SELECT media FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else None

# ---------------- METADATA ---------------- #
def set_metadata(user_id, metadata: dict):
    data = json.dumps(metadata)
    cursor.execute("UPDATE users SET metadata=? WHERE user_id=?", (data, user_id))
    conn.commit()

def get_metadata(user_id):
    cursor.execute("SELECT metadata FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return json.loads(row[0]) if row and row[0] else None

def set_metadata_status(user_id, status: bool):
    md = get_metadata(user_id) or {}
    md['status'] = status
    set_metadata(user_id, md)

def get_metadata_status(user_id):
    md = get_metadata(user_id)
    return md.get("status", False) if md else False

# ---------------- PREFIX ---------------- #
def set_prefix(user_id, text):
    cursor.execute("UPDATE users SET prefix=? WHERE user_id=?", (text, user_id))
    conn.commit()

def get_prefix(user_id):
    cursor.execute("SELECT prefix FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else None

# ---------------- SUFFIX ---------------- #
def set_suffix(user_id, text):
    cursor.execute("UPDATE users SET suffix=? WHERE user_id=?", (text, user_id))
    conn.commit()

def get_suffix(user_id):
    cursor.execute("SELECT suffix FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else None
