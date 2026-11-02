from dataclasses import dataclass

from budgeter.domain.transaction import Transaction
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

    def import_manual_entry(self, amount, merchant, date):
        transaction = Transaction(amount=amount, merchant=merchant, date=date)
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

    def _categorize_if_possible(self, transaction):
        if self.categorizer:
            transaction.category = self.categorizer.categorize(transaction)
