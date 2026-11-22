from pathlib import Path

# Keep the database in the src directory, regardless of where the app is launched.
DATABASE_PATH = Path(__file__).resolve().parent.parent / "budgeter.db"
