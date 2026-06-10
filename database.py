"""
database.py — SQLite bilan ishlash (CRUD operatsiyalar)
"""

import sqlite3
import logging
from datetime import datetime
from contextlib import contextmanager
from config import DB_PATH

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
# Ulanish menejeri
# ─────────────────────────────────────────

@contextmanager
def get_connection():
    """Thread-safe SQLite ulanish context manager."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"DB xatosi: {e}")
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────
# Jadval yaratish
# ─────────────────────────────────────────

def init_db() -> None:
    """Barcha jadvallarni yaratadi (agar mavjud bo'lmasa)."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                full_name   TEXT,
                joined_at   TEXT DEFAULT (datetime('now')),
                state       TEXT DEFAULT 'idle',
                temp_data   TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                amount      REAL    NOT NULL,
                category    TEXT    NOT NULL,
                note        TEXT    DEFAULT '',
                created_at  TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_expenses_user_date
                ON expenses(user_id, created_at);
        """)
    logger.info("Ma'lumotlar bazasi tayyor.")


# ─────────────────────────────────────────
# Foydalanuvchi operatsiyalari
# ─────────────────────────────────────────

def upsert_user(user_id: int, username: str, full_name: str) -> None:
    """Foydalanuvchini qo'shadi yoki yangilaydi."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO users (user_id, username, full_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username  = excluded.username,
                full_name = excluded.full_name
        """, (user_id, username, full_name))


def get_user_state(user_id: int) -> str:
    """Foydalanuvchi holatini qaytaradi."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT state FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
    return row["state"] if row else "idle"


def set_user_state(user_id: int, state: str, temp_data: str = "{}") -> None:
    """Foydalanuvchi holatini va vaqtinchalik ma'lumotni saqlaydi."""
    with get_connection() as conn:
        conn.execute("""
            UPDATE users SET state = ?, temp_data = ? WHERE user_id = ?
        """, (state, temp_data, user_id))


def get_temp_data(user_id: int) -> str:
    """Vaqtinchalik ma'lumotni qaytaradi (JSON string)."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT temp_data FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
    return row["temp_data"] if row else "{}"


# ─────────────────────────────────────────
# Xarajat operatsiyalari
# ─────────────────────────────────────────

def add_expense(user_id: int, amount: float, category: str, note: str = "") -> int:
    """Yangi xarajat qo'shadi, yangi id qaytaradi."""
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO expenses (user_id, amount, category, note)
            VALUES (?, ?, ?, ?)
        """, (user_id, amount, category, note))
    return cursor.lastrowid


def get_monthly_expenses(user_id: int, year: int, month: int) -> list[dict]:
    """Berilgan oy uchun xarajatlar ro'yxatini qaytaradi."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, amount, category, note, created_at
            FROM expenses
            WHERE user_id = ?
              AND strftime('%Y', created_at) = ?
              AND strftime('%m', created_at) = ?
            ORDER BY created_at DESC
        """, (user_id, str(year), f"{month:02d}")).fetchall()
    return [dict(r) for r in rows]


def get_monthly_summary(user_id: int, year: int, month: int) -> list[dict]:
    """Kategoriya bo'yicha umumiy xarajatlarni qaytaradi."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT category,
                   COUNT(*)       AS count,
                   SUM(amount)    AS total
            FROM expenses
            WHERE user_id = ?
              AND strftime('%Y', created_at) = ?
              AND strftime('%m', created_at) = ?
            GROUP BY category
            ORDER BY total DESC
        """, (user_id, str(year), f"{month:02d}")).fetchall()
    return [dict(r) for r in rows]


def delete_last_expense(user_id: int) -> bool:
    """Oxirgi xarajatni o'chiradi. Muvaffaqiyat bo'lsa True qaytaradi."""
    with get_connection() as conn:
        row = conn.execute("""
            SELECT id FROM expenses
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,)).fetchone()
        if not row:
            return False
        conn.execute("DELETE FROM expenses WHERE id = ?", (row["id"],))
    return True


def get_all_time_total(user_id: int) -> float:
    """Foydalanuvchining umumiy xarajatini qaytaradi."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = ?",
            (user_id,)
        ).fetchone()
    return row["total"] if row else 0.0
