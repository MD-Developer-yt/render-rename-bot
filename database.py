import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# ---------------- TABLE ---------------- #

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    caption TEXT,
    thumb TEXT,
    media TEXT DEFAULT 'document',
    metadata INTEGER DEFAULT 0
)
""")

conn.commit()


# ---------------- ADD USER ---------------- #

def add_user(user_id):

    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (user_id,)
    )

    conn.commit()


# ---------------- CAPTION ---------------- #

def set_caption(user_id, caption):

    cursor.execute(
        "UPDATE users SET caption=? WHERE user_id=?",
        (caption, user_id)
    )

    conn.commit()


def get_caption(user_id):

    cursor.execute(
        "SELECT caption FROM users WHERE user_id=?",
        (user_id,)
    )

    data = cursor.fetchone()

    if data and data[0]:
        return data[0]

    return None


# ---------------- THUMBNAIL ---------------- #

def set_thumb(user_id, path):

    cursor.execute(
        "UPDATE users SET thumb=? WHERE user_id=?",
        (path, user_id)
    )

    conn.commit()


def get_thumb(user_id):

    cursor.execute(
        "SELECT thumb FROM users WHERE user_id=?",
        (user_id,)
    )

    data = cursor.fetchone()

    if data:
        return data[0]

    return None


# ---------------- MEDIA MODE ---------------- #

def set_media(user_id, mode):

    cursor.execute(
        "UPDATE users SET media=? WHERE user_id=?",
        (mode, user_id)
    )

    conn.commit()


def get_media(user_id):

    cursor.execute(
        "SELECT media FROM users WHERE user_id=?",
        (user_id,)
    )

    data = cursor.fetchone()

    if data and data[0]:
        return data[0]

    return "document"


# ---------------- METADATA ---------------- #

def set_metadata_status(user_id, status):

    cursor.execute(
        "UPDATE users SET metadata=? WHERE user_id=?",
        (1 if status else 0, user_id)
    )

    conn.commit()


def get_metadata_status(user_id):

    cursor.execute(
        "SELECT metadata FROM users WHERE user_id=?",
        (user_id,)
    )

    data = cursor.fetchone()

    if data:
        return bool(data[0])

    return False
