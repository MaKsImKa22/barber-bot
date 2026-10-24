import sqlite3
from contextlib import closing
from pathlib import Path

DB_PATH = Path(__file__).with_name("bookings.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(_connect()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                service TEXT NOT NULL,
                day TEXT NOT NULL,
                hour INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (day, hour)
            )
            """
        )


def busy_hours(day):
    with closing(_connect()) as conn:
        rows = conn.execute("SELECT hour FROM bookings WHERE day = ?", (day,))
        return {row["hour"] for row in rows}


def add_booking(user_id, name, phone, service, day, hour):
    """Повертає id запису або None, якщо цей час уже зайнятий."""
    try:
        with closing(_connect()) as conn, conn:
            cur = conn.execute(
                "INSERT INTO bookings (user_id, name, phone, service, day, hour) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, name, phone, service, day, hour),
            )
            return cur.lastrowid
    except sqlite3.IntegrityError:
        return None


def get_booking(booking_id):
    with closing(_connect()) as conn:
        return conn.execute(
            "SELECT * FROM bookings WHERE id = ?", (booking_id,)
        ).fetchone()


def delete_booking(booking_id):
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))


def user_bookings(user_id, from_day):
    with closing(_connect()) as conn:
        return conn.execute(
            "SELECT * FROM bookings WHERE user_id = ? AND day >= ? ORDER BY day, hour",
            (user_id, from_day),
        ).fetchall()


def bookings_between(from_day, to_day):
    with closing(_connect()) as conn:
        return conn.execute(
            "SELECT * FROM bookings WHERE day BETWEEN ? AND ? ORDER BY day, hour",
            (from_day, to_day),
        ).fetchall()
