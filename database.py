import sqlite3
import os
import json

DB_PATH = "bot_data.db"

# -------- DATABASE SETUP --------
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# Users table
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    caption TEXT,
    thumb TEXT,
    media TEXT,
    metadata TEXT
)
""")
conn.commit()

# -------- USER FUNCTIONS --------
def add_user(user_id):
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

def total_users():
    c.execute("SELECT COUNT(*) FROM users")
    return c.fetchone()[0]

def get_users():
    c.execute("SELECT user_id FROM users")
    return [row[0] for row in c.fetchall()]

# -------- CAPTION --------
def set_caption(user_id, caption):
    c.execute("UPDATE users SET caption=? WHERE user_id=?", (caption, user_id))
    conn.commit()

def get_caption(user_id):
    c.execute("SELECT caption FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    return row[0] if row else None

def del_caption(user_id):
    c.execute("UPDATE users SET caption=NULL WHERE user_id=?", (user_id,))
    conn.commit()

# -------- THUMBNAIL --------
def set_thumb(user_id, path):
    c.execute("UPDATE users SET thumb=? WHERE user_id=?", (path, user_id))
    conn.commit()

def get_thumb(user_id):
    c.execute("SELECT thumb FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    return row[0] if row else None

def del_thumb(user_id):
    c.execute("UPDATE users SET thumb=NULL WHERE user_id=?", (user_id,))
    conn.commit()

# -------- MEDIA --------
def set_media(user_id, media_type):
    c.execute("UPDATE users SET media=? WHERE user_id=?", (media_type, user_id))
    conn.commit()

def get_media(user_id):
    c.execute("SELECT media FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    return row[0] if row else "document"

# -------- METADATA --------
def set_metadata(user_id, metadata: dict):
    data = json.dumps(metadata)
    c.execute("UPDATE users SET metadata=? WHERE user_id=?", (data, user_id))
    conn.commit()

def get_metadata(user_id):
    c.execute("SELECT metadata FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    return json.loads(row[0]) if row and row[0] else None

def get_metadata_status(user_id):
    md = get_metadata(user_id)
    return bool(md)

def del_metadata(user_id):
    c.execute("UPDATE users SET metadata=NULL WHERE user_id=?", (user_id,))
    conn.commit()
