import sqlite3
from contextlib import closing

from budgeter.domain.category import Category

DEFAULT_CATEGORIES = [
    Category("Food", ["uber eats", "starbucks", "publix", "mcdonalds", "chipotle", "restaurant", "cafe", "pizza", "grocery"]),
    Category("Transport", ["shell", "uber", "lyft", "chevron", "exxon", "parking"]),
    Category("Entertainment", ["netflix", "spotify", "hulu", "cinema"]),
    Category("Utilities", ["fpl", "comcast", "verizon", "water", "electric"]),
    Category("Shopping", ["amazon", "walmart", "target"]),
]


class CategoryRepository:
    """Persists Category objects and their keywords in the SQLite file.

    Categories come back in the order they were first saved, which is the
    order TransactionCategorization tries them in.
    """

    def __init__(self, db_path="budgeter.db"):
        self.db_path = str(db_path)
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE COLLATE NOCASE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS category_keywords (
                    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
                    keyword TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    PRIMARY KEY (category_id, keyword)
                )
                """
            )

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")  # needed for ON DELETE CASCADE
        return conn

    def save(self, category):
        """Insert the category, or replace its keywords if the name already exists."""
        with closing(self._connect()) as conn, conn:
            row = conn.execute("SELECT id FROM categories WHERE name = ?", (category.name,)).fetchone()
            if row is None:
                category_id = conn.execute("INSERT INTO categories (name) VALUES (?)", (category.name,)).lastrowid
            else:
                category_id = row[0]
                conn.execute("DELETE FROM category_keywords WHERE category_id = ?", (category_id,))
            conn.executemany(
                "INSERT INTO category_keywords (category_id, keyword, position) VALUES (?, ?, ?)",
                [(category_id, word, position) for position, word in enumerate(category.keywords)],
            )

    def find_all(self):
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT c.name, k.keyword FROM categories c "
                "LEFT JOIN category_keywords k ON k.category_id = c.id "
                "ORDER BY c.id, k.position"
            ).fetchall()
        grouped = {}
        for name, keyword in rows:
            grouped.setdefault(name, [])
            if keyword is not None:
                grouped[name].append(keyword)
        categories = []

        for name, words in grouped.items():
            try:
                categories.append(Category(name, words))
            except (ValueError, TypeError) as error:
                raise ValueError(
                    f"Stored category '{name}' is invalid: {error}"
                ) from error

        return categories

    def find_by_name(self, name):
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT id, name FROM categories WHERE name = ?",
                (name,),
            ).fetchone()

            if row is None:
                return None

            category_id, category_name = row

            keyword_rows = conn.execute(
                "SELECT keyword FROM category_keywords "
                "WHERE category_id = ? ORDER BY position",
                (category_id,),
            ).fetchall()

        keywords = [keyword for (keyword,) in keyword_rows]

        return Category(category_name, keywords)

    def delete(self, name):
        """Remove a category and its keywords. Returns True if one was removed."""
        with closing(self._connect()) as conn, conn:
            cursor = conn.execute("DELETE FROM categories WHERE name = ?", (name,))
        return cursor.rowcount > 0

    def seed_defaults(self):
        """Fill an EMPTY table with starter categories; never touches existing ones."""
        if self.find_all():
            return False
        for category in DEFAULT_CATEGORIES:
            self.save(category)
        return True
