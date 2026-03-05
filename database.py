import sqlite3
import json
import os

DB_NAME = "bot.db"

# Ensure DB exists
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

# Users table
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    caption TEXT,
    thumb TEXT,
    media TEXT DEFAULT 'document',
    metadata_status INTEGER DEFAULT 0,
    metadata TEXT
)
""")
conn.commit()
conn.close()


# ---------------- USER FUNCTIONS ---------------- #

def add_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
    conn.commit()
    conn.close()


def total_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count


def get_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users


# ---------------- CAPTION ---------------- #

def set_caption(user_id, caption):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET caption=? WHERE user_id=?", (caption, user_id))
    conn.commit()
    conn.close()


def get_caption(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT caption FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result and result[0] else None


# ---------------- THUMBNAIL ---------------- #

def set_thumb(user_id, path):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET thumb=? WHERE user_id=?", (path, user_id))
    conn.commit()
    conn.close()


def get_thumb(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT thumb FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result and result[0] else None


# ---------------- MEDIA ---------------- #

def set_media(user_id, mode):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET media=? WHERE user_id=?", (mode, user_id))
    conn.commit()
    conn.close()


def get_media(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT media FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else "document"


# ---------------- METADATA ---------------- #

def set_metadata(user_id, metadata_dict):
    metadata_json = json.dumps(metadata_dict)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET metadata=? WHERE user_id=?", (metadata_json, user_id))
    conn.commit()
    conn.close()


def get_metadata(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT metadata FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return json.loads(result[0]) if result and result[0] else None


def set_metadata_status(user_id, status: bool):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET metadata_status=? WHERE user_id=?", (1 if status else 0, user_id))
    conn.commit()
    conn.close()


def get_metadata_status(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT metadata_status FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return bool(result[0]) if result else False
