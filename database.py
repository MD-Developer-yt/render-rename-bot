import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    caption TEXT,
    media TEXT DEFAULT 'document',
    thumb TEXT,
    metadata TEXT DEFAULT '{}',
    meta_status INTEGER DEFAULT 0
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
    r = cur.fetchone()
    return r[0] if r else None


def set_media(uid, media):
    cur.execute("UPDATE users SET media=? WHERE user_id=?", (media, uid))
    conn.commit()


def get_media(uid):
    cur.execute("SELECT media FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    return r[0] if r else "document"


def set_thumb(uid, path):
    cur.execute("UPDATE users SET thumb=? WHERE user_id=?", (path, uid))
    conn.commit()


def get_thumb(uid):
    cur.execute("SELECT thumb FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    return r[0] if r else None


def set_metadata(uid, meta):
    cur.execute("UPDATE users SET metadata=? WHERE user_id=?", (meta, uid))
    conn.commit()


def get_metadata(uid):
    cur.execute("SELECT metadata FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    return r[0] if r else "{}"


def set_meta_status(uid, status):
    cur.execute("UPDATE users SET meta_status=? WHERE user_id=?", (1 if status else 0, uid))
    conn.commit()


def get_meta_status(uid):
    cur.execute("SELECT meta_status FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    return bool(r[0]) if r else False
