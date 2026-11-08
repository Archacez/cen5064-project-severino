import sqlite3
from contextlib import closing

from budgeter.domain.budget import Budget


class BudgetRepository:
    """Persists Budget objects (one limit per category) in the SQLite file."""

    def __init__(self, db_path="budgeter.db"):
        self.db_path = str(db_path)
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS budgets (
                    category TEXT PRIMARY KEY COLLATE NOCASE,
                    limit_amount REAL NOT NULL
                )
                """
            )

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def save(self, budget):
        """Insert the budget, or replace the limit if the category already has one."""
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO budgets (category, limit_amount) VALUES (?, ?) "
                "ON CONFLICT(category) DO UPDATE SET limit_amount = excluded.limit_amount",
                (budget.category, budget.limit),
            )

    def find_by_category(self, category):
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT category, limit_amount FROM budgets WHERE category = ?",
                (category,),
            ).fetchone()
        return Budget(*row) if row else None

    def find_all(self):
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT category, limit_amount FROM budgets ORDER BY category"
            ).fetchall()
        return [Budget(*row) for row in rows]

    def delete(self, category):
        """Remove a budget. Returns True if one was removed."""
        with closing(self._connect()) as conn, conn:
            cursor = conn.execute("DELETE FROM budgets WHERE category = ?", (category,))
        return cursor.rowcount > 0
