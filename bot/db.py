"""SQLite storage: one table of entries, one table of monthly limits."""

import sqlite3
from contextlib import closing
from datetime import datetime

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    is_income INTEGER NOT NULL,
    category TEXT NOT NULL,
    note TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_entries_user ON entries(user_id, created_at);
CREATE TABLE IF NOT EXISTS limits (user_id INTEGER PRIMARY KEY, monthly REAL NOT NULL);
"""


class Store:
    def __init__(self, path: str):
        self.path = path
        with closing(self._conn()) as c:
            c.executescript(SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.path, timeout=30)
        c.execute("PRAGMA journal_mode=WAL")
        return c

    def add(self, user_id, amount, is_income, category, note, when: datetime | None = None) -> int:
        when = when or datetime.now()
        with closing(self._conn()) as c, c:
            cur = c.execute(
                "INSERT INTO entries(user_id, amount, is_income, category, note, created_at)"
                " VALUES (?,?,?,?,?,?)",
                (
                    user_id,
                    amount,
                    int(is_income),
                    category,
                    note,
                    when.isoformat(timespec="seconds"),
                ),
            )
            return cur.lastrowid

    def undo(self, user_id) -> tuple | None:
        """Delete and return the user's latest entry (amount, is_income, category, note)."""
        with closing(self._conn()) as c, c:
            row = c.execute(
                "SELECT id, amount, is_income, category, note FROM entries"
                " WHERE user_id=? ORDER BY id DESC LIMIT 1",
                (user_id,),
            ).fetchone()
            if not row:
                return None
            c.execute("DELETE FROM entries WHERE id=?", (row[0],))
            return row[1:]

    def last(self, user_id, n=10) -> list[tuple]:
        with closing(self._conn()) as c:
            return c.execute(
                "SELECT created_at, amount, is_income, category, note FROM entries"
                " WHERE user_id=? ORDER BY id DESC LIMIT ?",
                (user_id, n),
            ).fetchall()

    def summary(self, user_id, prefix: str) -> dict:
        """prefix: 'YYYY-MM' or 'YYYY-MM-DD'. Returns income, expense and expense by category."""
        with closing(self._conn()) as c:
            rows = c.execute(
                "SELECT is_income, category, SUM(amount) FROM entries"
                " WHERE user_id=? AND created_at LIKE ? GROUP BY is_income, category",
                (user_id, prefix + "%"),
            ).fetchall()
        income = sum(r[2] for r in rows if r[0])
        by_cat = {r[1]: r[2] for r in rows if not r[0]}
        return {
            "income": income,
            "expense": sum(by_cat.values()),
            "by_category": dict(sorted(by_cat.items(), key=lambda kv: -kv[1])),
        }

    def all_entries(self, user_id) -> list[tuple]:
        with closing(self._conn()) as c:
            return c.execute(
                "SELECT created_at, is_income, category, amount, note FROM entries"
                " WHERE user_id=? ORDER BY id",
                (user_id,),
            ).fetchall()

    def set_limit(self, user_id, monthly: float) -> None:
        with closing(self._conn()) as c, c:
            c.execute(
                "INSERT INTO limits VALUES (?,?) ON CONFLICT(user_id) DO UPDATE SET"
                " monthly=excluded.monthly",
                (user_id, monthly),
            )

    def get_limit(self, user_id) -> float | None:
        with closing(self._conn()) as c:
            row = c.execute("SELECT monthly FROM limits WHERE user_id=?", (user_id,)).fetchone()
        return row[0] if row else None
