from dataclasses import dataclass

import pandas as pd

from budgeter.domain.transaction import Transaction

REQUIRED_COLUMNS = {"amount", "merchant", "date"}
THOUSANDS_AMOUNT = r"[0-9]{1,3}(,[0-9]{3})+(\.[0-9]+)?"  # e.g. 1,234.50


@dataclass(frozen=True)
class ImportResult:
    """What one CSV import did: the saved transactions and how many rows were refused."""

    imported: list
    skipped: int


class TransactionImportService:
    """Orchestrates the import flow: parse -> (categorize) -> save.

    Parsing (turning file text into values) is this tier's job. Deciding
    whether a transaction is VALID is the Domain's job: both manual entry
    and CSV rows are accepted or rejected by the Transaction constructor.

    The repository is any object with save(transaction) and find_all().
    The service keeps no per-import state: import_csv() returns an
    ImportResult, so the Presentation tier can report what happened
    (the service itself never prints).
    """

    def __init__(self, repository, categorizer=None):
        self.repository = repository
        self.categorizer = categorizer

    def import_manual_entry(self, amount, merchant, date):
        transaction = Transaction(amount=amount, merchant=merchant, date=date)
        self._categorize_if_possible(transaction)
        self.repository.save(transaction)
        return transaction

    def import_csv(self, file_path):
        try:
            # Read everything as plain text and only blank cells count as missing.
            # pandas' defaults would turn merchants like "NA" or "None" into NaN
            # and would guess types (e.g. "0001" -> 1) before we validate.
            df = pd.read_csv(
                file_path, dtype=str, keep_default_na=False, na_values=[""]
            )
        except pd.errors.EmptyDataError:
            raise ValueError("CSV file is empty") from None

        # Check the schema BEFORE touching any column.
        df.columns = df.columns.astype(str).str.strip().str.lower()
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"CSV is missing required column(s): {sorted(missing)}")

        # pandas does the cleaning and type coercion only. Unparseable
        # amounts become NaN; the Domain will reject them.
        amount_text = df["amount"].astype("string").str.strip()
        has_separators = amount_text.str.fullmatch(THOUSANDS_AMOUNT).fillna(False)
        amount_text = amount_text.where(
            ~has_separators, amount_text.str.replace(",", "", regex=False)
        )
        amounts = pd.to_numeric(amount_text, errors="coerce").astype("float64")
        merchants = df["merchant"].astype("string").str.strip().fillna("")
        dates = df["date"].astype("string").str.strip()

        imported = []
        for amount, merchant, date in zip(amounts, merchants, dates):
            try:
                transaction = Transaction(amount=amount, merchant=merchant, date=date)
            except ValueError:
                continue  # the Domain refused this row
            self._categorize_if_possible(transaction)
            self.repository.save(transaction)
            imported.append(transaction)

        return ImportResult(imported=imported, skipped=len(df) - len(imported))

    def list_transactions(self):
        return self.repository.find_all()

    def _categorize_if_possible(self, transaction):
        if self.categorizer:
            transaction.category = self.categorizer.categorize(transaction)
