
import pandas as pd

REQUIRED_COLUMNS = {"amount", "merchant", "date"}
THOUSANDS_AMOUNT = r"[0-9]{1,3}(,[0-9]{3})+(\.[0-9]+)?"


class TransactionCsvParser:
    """Reads CSV files and prepares transaction fields for validation."""

    def parse(self, file_path):
        try:
            df = pd.read_csv(
                file_path, dtype=str, keep_default_na=False, na_values=[""]
            )
        except pd.errors.EmptyDataError:
            raise ValueError("CSV file is empty") from None

        df.columns = df.columns.astype(str).str.strip().str.lower()
        missing = REQUIRED_COLUMNS - set(df.columns)

        if missing:
            raise ValueError(
                f"CSV is missing required column(s): {sorted(missing)}"
            )

        amount_text = df["amount"].astype("string").str.strip()
        has_separators = (
            amount_text.str.fullmatch(THOUSANDS_AMOUNT).fillna(False)
        )
        amount_text = amount_text.where(
            ~has_separators,
            amount_text.str.replace(",", "", regex=False),
        )
        amounts = pd.to_numeric(
            amount_text, errors="coerce"
        ).astype("float64")

        merchants = (
            df["merchant"].astype("string").str.strip().fillna("")
        )
        dates = df["date"].astype("string").str.strip()

        if "transaction_type" in df.columns:
            transaction_types = (
                df["transaction_type"]
                .astype("string")
                .str.strip()
                .str.lower()
            )
            transaction_types = transaction_types.replace("", "expense")
        else:
            transaction_types = pd.Series(
                ["expense"] * len(df), dtype="string"
            )

        valid_types = {"income", "expense"}
        invalid_types = ~transaction_types.isin(valid_types)

        if invalid_types.any():
            invalid_values = sorted(
                transaction_types[invalid_types].unique().tolist()
            )
            raise ValueError(
                f"Invalid transaction type(s): {invalid_values}. "
                "Expected 'income' or 'expense'."
            )

        return zip(amounts, merchants, dates, transaction_types), len(df)
