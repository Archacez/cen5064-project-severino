from dataclasses import dataclass

from budgeter.domain.transaction import Transaction, TransactionType
from budgeter.service.transaction_csv_parser import TransactionCsvParser


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

    def __init__(self, repository, categorizer=None, csv_parser=None):
        self.repository = repository
        self.categorizer = categorizer
        self.csv_parser = csv_parser or TransactionCsvParser()

    def import_manual_entry(
        self,
        amount,
        merchant,
        date,
        transaction_type=TransactionType.EXPENSE,
        category=None,
    ):
        transaction = Transaction(
            amount=amount,
            merchant=merchant,
            date=date,
            category=category,
            transaction_type=transaction_type,
        )

        self._categorize_if_possible(transaction)
        self.repository.save(transaction)
        return transaction

    def import_csv(self, file_path):
        rows, total_rows = self.csv_parser.parse(file_path)

        imported = []
        for amount, merchant, date in rows:
            try:
                transaction = Transaction(
                    amount=amount, merchant=merchant, date=date
                )
            except ValueError:
                continue

            self._categorize_if_possible(transaction)
            self.repository.save(transaction)
            imported.append(transaction)

        return ImportResult(
            imported=imported,
            skipped=total_rows - len(imported),
        )

    def list_transactions(self):
        return self.repository.find_all()

    def list_transaction_records(self):
        """Return transaction records including their database IDs."""
        return self.repository.find_all_records()

    def update_transaction(
        self,
        transaction_id,
        amount,
        merchant,
        date,
        transaction_type=None,
        category=None,
    ):
        """Validate and update an existing transaction."""
        existing = self.repository.find_record_by_id(transaction_id)

        if existing is None:
            return False

        if transaction_type is None:
            transaction_type = existing["transaction_type"]

        transaction_type = TransactionType(transaction_type)

        if transaction_type == TransactionType.INCOME:
            if category is None and existing["transaction_type"] == "income":
                category = existing["category"]
        else:
            category = None

        transaction = Transaction(
            amount=amount,
            merchant=merchant,
            date=date,
            category=category,
            transaction_type=transaction_type,
        )

        self._categorize_if_possible(transaction)

        return self.repository.update(transaction_id, transaction)

    def delete_transaction(self, transaction_id):
        """Delete a transaction by its database ID."""
        return self.repository.delete(transaction_id)

    def _categorize_if_possible(self, transaction):
        if (
            self.categorizer
            and transaction.transaction_type == TransactionType.EXPENSE
        ):
            transaction.category = self.categorizer.categorize(transaction)
