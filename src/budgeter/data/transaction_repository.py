
import sqlite3
from contextlib import closing

from budgeter.domain.transaction import Transaction


class TransactionRepository:
    """Persists and retrieves Transaction objects in SQLite."""

    def __init__(self, db_path="budgeter.db"):
        self.db_path = str(db_path)
        self._create_table()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    merchant TEXT NOT NULL,
                    date TEXT NOT NULL,
                    category TEXT,
                    transaction_type TEXT NOT NULL DEFAULT 'expense'
                        CHECK (transaction_type IN ('income', 'expense'))
                )
                """
            )
            columns = {
                row[1]
                for row in conn.execute("PRAGMA table_info(transactions)")
            }

            if "transaction_type" not in columns:
                conn.execute(
                    """
                    ALTER TABLE transactions
                    ADD COLUMN transaction_type TEXT NOT NULL DEFAULT 'expense'
                    CHECK (transaction_type IN ('income', 'expense'))
                    """
                )

    def save(self, transaction):
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                INSERT INTO transactions (
                    amount, merchant, date, category, transaction_type
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    transaction.amount,
                    transaction.merchant,
                    transaction.date,
                    transaction.category,
                    transaction.transaction_type.value,
                ),
            )

    def find_all(self):
        with closing(self._connect()) as conn:
            rows = conn.execute(
                """
                SELECT amount, merchant, date, category, transaction_type
                FROM transactions
                ORDER BY date, id
                """
            ).fetchall()

        return [self._to_transaction(row) for row in rows]

    def find_all_records(self):
        """Return transactions with their database IDs for CRUD operations."""
        with closing(self._connect()) as conn:
            rows = conn.execute(
                """
                SELECT id, amount, merchant, date, category, transaction_type
                FROM transactions
                ORDER BY date, id
                """
            ).fetchall()

        return [
            {
                "id": row[0],
                "amount": row[1],
                "merchant": row[2],
                "date": row[3],
                "category": row[4],
                "transaction_type": row[5],
            }
            for row in rows
        ]

    def find_record_by_id(self, transaction_id):
        with closing(self._connect()) as conn:
            row = conn.execute(
                """
                SELECT id, amount, merchant, date, category, transaction_type
                FROM transactions
                WHERE id = ?
                """,
                (transaction_id,),
            ).fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "amount": row[1],
            "merchant": row[2],
            "date": row[3],
            "category": row[4],
            "transaction_type": row[5],
        }

    def find_by_category(self, category):
        with closing(self._connect()) as conn:
            rows = conn.execute(
                """
                SELECT amount, merchant, date, category, transaction_type
                FROM transactions
                WHERE category IS ?
                ORDER BY date, id
                """,
                (category,),
            ).fetchall()

        return [self._to_transaction(row) for row in rows]

    def update(self, transaction_id, transaction):
        with closing(self._connect()) as conn, conn:
            cursor = conn.execute(
                """
                UPDATE transactions
                SET amount = ?, merchant = ?, date = ?, category = ?,
                    transaction_type = ?
                WHERE id = ?
                """,
                (
                    transaction.amount,
                    transaction.merchant,
                    transaction.date,
                    transaction.category,
                    transaction.transaction_type.value,
                    transaction_id,
                ),
            )

        return cursor.rowcount > 0

    def delete(self, transaction_id):
        with closing(self._connect()) as conn, conn:
            cursor = conn.execute(
                "DELETE FROM transactions WHERE id = ?",
                (transaction_id,),
            )

        return cursor.rowcount > 0

    @staticmethod
    def _to_transaction(row):
        amount, merchant, date, category, transaction_type = row

        return Transaction(
            amount=amount,
            merchant=merchant,
            date=date,
            category=category,
            transaction_type=transaction_type,
        )
