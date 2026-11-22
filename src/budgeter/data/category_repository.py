import json
import sqlite3
from contextlib import closing
from pathlib import Path

from budgeter.domain.category import Category

DEFAULT_CATEGORIES_FILE = Path(__file__).with_name("default_categories.json")


def load_default_categories():
    """Load starter categories from the JSON configuration file."""
    with DEFAULT_CATEGORIES_FILE.open(encoding="utf-8") as file:
        data = json.load(file)

    return [
        Category(item["name"], item["keywords"])
        for item in data
    ]


DEFAULT_CATEGORIES = load_default_categories()



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
            conn.execute(
                """
                UPDATE categories
                SET name = 'Transportation'
                WHERE name = 'Transport'
                """
            )
            transactions_table_exists = conn.execute(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table'
                AND name = 'transactions'
                """
            ).fetchone()

            if transactions_table_exists:
                conn.execute(
                    """
                    UPDATE transactions
                    SET category = 'Transportation'
                    WHERE category = 'Transport'
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
        """Add missing default categories without modifying existing ones."""
        existing_categories = {
            category.name.lower()
            for category in self.find_all()
        }

        added_category = False

        for category in DEFAULT_CATEGORIES:
            if category.name.lower() not in existing_categories:
                self.save(category)
                added_category = True

        return added_category