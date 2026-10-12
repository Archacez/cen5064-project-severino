import sqlite3
from contextlib import closing

from budgeter.domain.transaction import Transaction


class TransactionRepository:
    """Persists and retrieves Transaction objects in a SQLite file.

    This is the only class that knows SQL. Everything above it deals
    in Transaction objects.
    """

    def __init__(self, db_path="budgeter.db"):
        self.db_path = str(db_path)
        self._create_table()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        # "with conn" commits on success and rolls back on error;
        # closing() makes sure the connection is always closed.
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    merchant TEXT NOT NULL,
                    date TEXT NOT NULL,
                    category TEXT
                )
                """
            )

    def save(self, transaction):
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO transactions (amount, merchant, date, category) "
                "VALUES (?, ?, ?, ?)",
                (
                    transaction.amount,
                    transaction.merchant,
                    transaction.date,
                    transaction.category,
                ),
            )

    def find_all(self):
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT amount, merchant, date, category "
                "FROM transactions ORDER BY date, id"
            ).fetchall()
        return [self._to_transaction(row) for row in rows]

    def find_by_category(self, category):
        # "IS ?" (not "= ?") so that category=None matches NULL rows.
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT amount, merchant, date, category "
                "FROM transactions WHERE category IS ? ORDER BY date, id",
                (category,),
            ).fetchall()
        return [self._to_transaction(row) for row in rows]

    @staticmethod
    def _to_transaction(row):
        amount, merchant, date, category = row
        return Transaction(
            amount=amount, merchant=merchant, date=date, category=category
        )
