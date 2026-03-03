import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    caption TEXT,
    thumb TEXT,
    media TEXT DEFAULT 'document',
    meta_enabled INTEGER DEFAULT 1,

    title TEXT,
    audio TEXT,
    author TEXT,
    video TEXT,
    subtitle TEXT,
    artist TEXT,
    encoded_by TEXT
)
""")

conn.commit()


# ---------------- BASIC USER ---------------- #

def add_user(uid):
    cur.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (uid,))
    conn.commit()


def get_all_users():
    cur.execute("SELECT user_id FROM users")
    return [x[0] for x in cur.fetchall()]


# ---------------- CAPTION ---------------- #

def set_caption(uid, text):
    cur.execute("UPDATE users SET caption=? WHERE user_id=?", (text, uid))
    conn.commit()


def get_caption(uid):
    cur.execute("SELECT caption FROM users WHERE user_id=?", (uid,))
    data = cur.fetchone()
    return data[0] if data and data[0] else None


def remove_caption(uid):
    cur.execute("UPDATE users SET caption=NULL WHERE user_id=?", (uid,))
    conn.commit()


# ---------------- THUMB ---------------- #

def set_thumb(uid, path):
    cur.execute("UPDATE users SET thumb=? WHERE user_id=?", (path, uid))
    conn.commit()


def get_thumb(uid):
    cur.execute("SELECT thumb FROM users WHERE user_id=?", (uid,))
    data = cur.fetchone()
    return data[0] if data and data[0] else None


def remove_thumb(uid):
    cur.execute("UPDATE users SET thumb=NULL WHERE user_id=?", (uid,))
    conn.commit()


# ---------------- MEDIA ---------------- #

def set_media(uid, m):
    cur.execute("UPDATE users SET media=? WHERE user_id=?", (m, uid))
    conn.commit()


def get_media(uid):
    cur.execute("SELECT media FROM users WHERE user_id=?", (uid,))
    data = cur.fetchone()
    return data[0] if data else "document"


# ---------------- META TOGGLE ---------------- #

def set_meta_status(uid, status):
    cur.execute("UPDATE users SET meta_enabled=? WHERE user_id=?", (status, uid))
    conn.commit()


def get_meta_status(uid):
    cur.execute("SELECT meta_enabled FROM users WHERE user_id=?", (uid,))
    data = cur.fetchone()
    return data[0] if data else 1


# ---------------- METADATA ---------------- #

def set_metadata(uid, data):
    cur.execute("""
        UPDATE users SET
        title=?,
        audio=?,
        author=?,
        video=?,
        subtitle=?,
        artist=?,
        encoded_by=?
        WHERE user_id=?
    """, (
        data.get("title"),
        data.get("audio"),
        data.get("author"),
        data.get("video"),
        data.get("subtitle"),
        data.get("artist"),
        data.get("encoded_by"),
        uid
    ))
    conn.commit()


def get_metadata(uid):
    cur.execute("""
        SELECT title, audio, author, video,
               subtitle, artist, encoded_by
        FROM users WHERE user_id=?
    """, (uid,))
    data = cur.fetchone()

    if not data:
        return None

    keys = [
        "title",
        "audio",
        "author",
        "video",
        "subtitle",
        "artist",
        "encoded_by"
    ]

    return dict(zip(keys, data))
