import sqlite3

DB_PATH = "database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # جدول الفعاليات
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            location TEXT NOT NULL,
            seats INTEGER NOT NULL,
            booked INTEGER DEFAULT 0,
            user_id INTEGER
        )
    """)
    # جدول المستخدمين
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_all_events():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM events")
    events = cur.fetchall()
    conn.close()
    return events

def add_event(name, date, location, seats, user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO events (name, date, location, seats, user_id) VALUES (?, ?, ?, ?, ?)",
                (name, date, location, seats, user_id))
    conn.commit()
    conn.close()

def book_seat(event_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT seats, booked FROM events WHERE id = ?", (event_id,))
    row = cur.fetchone()
    if row and row[1] < row[0]:
        cur.execute("UPDATE events SET booked = booked + 1 WHERE id = ?", (event_id,))
        conn.commit()
        result = True
    else:
        result = False
    conn.close()
    return result

def add_user(username, password_hash):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # المستخدم موجود مسبقًا
    finally:
        conn.close()

def get_user_by_username(username):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()
    return user
