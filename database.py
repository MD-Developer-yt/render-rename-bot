import sqlite3

conn = sqlite3.connect("users.db", check_same_thread=False)
db = conn.cursor()

db.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    caption TEXT,
    thumb TEXT,
    media_type TEXT
)
""")
conn.commit()

def add_user(user_id):
    db.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
    conn.commit()

def set_caption(user_id, caption):
    db.execute("UPDATE users SET caption=? WHERE user_id=?", (caption, user_id))
    conn.commit()

def get_caption(user_id):
    db.execute("SELECT caption FROM users WHERE user_id=?", (user_id,))
    r = db.fetchone()
    return r[0] if r else None

def set_thumb(user_id, path):
    db.execute("UPDATE users SET thumb=? WHERE user_id=?", (path, user_id))
    conn.commit()

def get_thumb(user_id):
    db.execute("SELECT thumb FROM users WHERE user_id=?", (user_id,))
    r = db.fetchone()
    return r[0] if r else None

def set_media(user_id, mtype):
    db.execute("UPDATE users SET media_type=? WHERE user_id=?", (mtype, user_id))
    conn.commit()

def get_media(user_id):
    db.execute("SELECT media_type FROM users WHERE user_id=?", (user_id,))
    r = db.fetchone()
    return r[0] if r else "file"
