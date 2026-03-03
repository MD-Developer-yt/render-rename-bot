import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

# Create users table
cur.execute("""CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    caption TEXT,
    thumb TEXT,
    media TEXT DEFAULT 'document',
    metadata_title TEXT,
    metadata_audio TEXT,
    metadata_author TEXT,
    metadata_video TEXT,
    metadata_subtitle TEXT,
    metadata_artist TEXT,
    metadata_encoded TEXT,
    meta_enabled INTEGER DEFAULT 1
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

def remove_caption(uid):
    cur.execute("UPDATE users SET caption=NULL WHERE user_id=?", (uid,))
    conn.commit()

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

def set_media(uid, m):
    cur.execute("UPDATE users SET media=? WHERE user_id=?", (m, uid))
    conn.commit()

def get_media(uid):
    cur.execute("SELECT media FROM users WHERE user_id=?", (uid,))
    data = cur.fetchone()
    return data[0] if data else "document"

def set_metadata(uid, meta_dict):
    cur.execute("""
        UPDATE users SET 
        metadata_title=?,
        metadata_audio=?,
        metadata_author=?,
        metadata_video=?,
        metadata_subtitle=?,
        metadata_artist=?,
        metadata_encoded=?
        WHERE user_id=?
    """, (
        meta_dict.get("title"),
        meta_dict.get("audio"),
        meta_dict.get("author"),
        meta_dict.get("video"),
        meta_dict.get("subtitle"),
        meta_dict.get("artist"),
        meta_dict.get("encoded_by"),
        uid
    ))
    conn.commit()

def get_metadata(uid):
    cur.execute("""
        SELECT metadata_title, metadata_audio, metadata_author, metadata_video,
        metadata_subtitle, metadata_artist, metadata_encoded, meta_enabled
        FROM users WHERE user_id=?
    """, (uid,))
    data = cur.fetchone()
    if data:
        return {
            "title": data[0],
            "audio": data[1],
            "author": data[2],
            "video": data[3],
            "subtitle": data[4],
            "artist": data[5],
            "encoded_by": data[6],
            "meta_enabled": bool(data[7])
        }
    return None

def toggle_meta(uid, enable: bool):
    cur.execute("UPDATE users SET meta_enabled=? WHERE user_id=?", (1 if enable else 0, uid))
    conn.commit()

def get_all_users():
    cur.execute("SELECT user_id FROM users")
    return [i[0] for i in cur.fetchall()]
