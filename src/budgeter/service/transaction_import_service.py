import csv

from budgeter.domain.transaction import Transaction


class TransactionImportService:
    "Orchestrates the import flow: parse -> (categorize) -> save."

    def __init__(self, repository, categorizer=None):
        self.repository = repository
        self.categorizer = categorizer

    def import_manual_entry(self, amount, merchant, date):
        transaction = Transaction(amount=amount, merchant=merchant, date=date)
        self._categorize_if_possible(transaction)
        self.repository.save(transaction)
        return transaction

    def import_csv(self, file_path):
        imported = []
        skipped = []
        with open(file_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row_num, row in enumerate(reader, start=2):  # row 1 is the header
                try:
                    transaction = Transaction(
                        amount=float(row["amount"]),
                        merchant=row["merchant"],
                        date=row["date"],
                    )
                except (KeyError, ValueError) as e:
                    skipped.append((row_num, str(e)))
                    continue

                self._categorize_if_possible(transaction)
                self.repository.save(transaction)
                imported.append(transaction)

        if skipped:
            print(f"Skipped {len(skipped)} malformed row(s): {skipped}")

        return imported

    def _categorize_if_possible(self, transaction):
        if self.categorizer:
            transaction.category = self.categorizer.categorize(transaction)
