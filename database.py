import sqlite3
import os

DB_PATH = "bot.db"

os.makedirs("data", exist_ok=True)
conn = sqlite3.connect(os.path.join("data", DB_PATH), check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    caption TEXT,
    thumb TEXT,
    media TEXT DEFAULT 'document',
    metadata TEXT
)
""")
conn.commit()


def add_user(uid):
    cur.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (uid,))
    conn.commit()


def set_caption(uid, text):
    cur.execute("UPDATE users SET caption=? WHERE user_id=?", (text, uid))
    conn.commit()


def get_caption(uid):
    cur.execute("SELECT caption FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    return row[0] if row and row[0] else None


def remove_caption(uid):
    cur.execute("UPDATE users SET caption=NULL WHERE user_id=?", (uid,))
    conn.commit()


def set_thumb(uid, path):
    cur.execute("UPDATE users SET thumb=? WHERE user_id=?", (path, uid))
    conn.commit()


def get_thumb(uid):
    cur.execute("SELECT thumb FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    return row[0] if row and row[0] else None


def remove_thumb(uid):
    cur.execute("UPDATE users SET thumb=NULL WHERE user_id=?", (uid,))
    conn.commit()


def set_media(uid, media_type):
    cur.execute("UPDATE users SET media=? WHERE user_id=?", (media_type, uid))
    conn.commit()


def get_media(uid):
    cur.execute("SELECT media FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    return row[0] if row else "document"


def set_metadata(uid, meta_dict):
    import json
    cur.execute("UPDATE users SET metadata=? WHERE user_id=?", (json.dumps(meta_dict), uid))
    conn.commit()


def get_metadata(uid):
    import json
    cur.execute("SELECT metadata FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    if row and row[0]:
        return json.loads(row[0])
    return None
