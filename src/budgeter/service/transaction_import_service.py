import pandas as pd

from budgeter.domain.transaction import Transaction


class TransactionImportService:
    """Orchestrates the import flow: parse -> (categorize) -> save.

    categorizer is optional for now - wired in when issue #2
    (auto-categorization) is implemented. Depends on
    TransactionRepositoryInterface, not a concrete repository class.
    """

    def __init__(self, repository, categorizer=None):
        self.repository = repository
        self.categorizer = categorizer

    def import_manual_entry(self, amount, merchant, date):
        if amount is None or amount <= 0:
            raise ValueError(f"Invalid amount: {amount!r} (must be a positive number)")
        if not merchant or not merchant.strip():
            raise ValueError("Merchant cannot be empty")
        if not date or not str(date).strip():
            raise ValueError("Date cannot be empty")

        transaction = Transaction(amount=amount, merchant=merchant, date=date)
        self._categorize_if_possible(transaction)
        self.repository.save(transaction)
        return transaction

    def import_csv(self, file_path):
        df = pd.read_csv(file_path)

        # Coerce bad values to NaN instead of raising - this is the
        # pandas equivalent of the try/except-per-row approach.
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        df["merchant"] = df["merchant"].astype(str).str.strip()

        required_cols = {"amount", "merchant", "date"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            raise ValueError(f"CSV is missing required column(s): {missing_cols}")

        # Drop rows that failed to parse (malformed amount) or have
        # an empty/blank merchant - this replaces the row-by-row
        # try/except skip logic from the previous version.
        clean_df = df.dropna(subset=["amount", "merchant", "date"])
        clean_df = clean_df[clean_df["merchant"] != ""]

        imported = []
        for _, row in clean_df.iterrows():
            transaction = Transaction(
                amount=float(row["amount"]),
                merchant=row["merchant"],
                date=row["date"],
            )
            self._categorize_if_possible(transaction)
            self.repository.save(transaction)
            imported.append(transaction)

        skipped_count = len(df) - len(clean_df)
        if skipped_count:
            print(f"Skipped {skipped_count} malformed row(s).")

        return imported

    def _categorize_if_possible(self, transaction):
        if self.categorizer:
            transaction.category = self.categorizer.categorize(transaction)
