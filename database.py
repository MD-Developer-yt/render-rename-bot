import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    caption TEXT,
    thumb TEXT,
    media TEXT DEFAULT 'document',
    metadata TEXT DEFAULT '{}'
)""")
conn.commit()

def add_user(uid):
    cur.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (uid,))
    conn.commit()

def set_caption(uid, text):
    cur.execute("UPDATE users SET caption=? WHERE user_id=?", (text, uid))
    conn.commit()

def get_caption(uid):
    cur.execute("SELECT caption FROM users WHERE user_id=?", (uid,))
    data = cur.fetchone()
    return data[0] if data and data[0] else None

def set_thumb(uid, path):
    cur.execute("UPDATE users SET thumb=? WHERE user_id=?", (path, uid))
    conn.commit()

def get_thumb(uid):
    cur.execute("SELECT thumb FROM users WHERE user_id=?", (uid,))
    data = cur.fetchone()
    return data[0] if data and data[0] else None

def set_media(uid, mode):
    cur.execute("UPDATE users SET media=? WHERE user_id=?", (mode, uid))
    conn.commit()

def get_media(uid):
    cur.execute("SELECT media FROM users WHERE user_id=?", (uid,))
    data = cur.fetchone()
    return data[0] if data else "document"

def set_metadata(uid, meta):
    cur.execute("UPDATE users SET metadata=? WHERE user_id=?", (meta, uid))
    conn.commit()

def get_metadata(uid):
    cur.execute("SELECT metadata FROM users WHERE user_id=?", (uid,))
    data = cur.fetchone()
    return data[0] if data else "{}"
