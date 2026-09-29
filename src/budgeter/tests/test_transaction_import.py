import csv

from budgeter.service.transaction_import_service import TransactionImportService


class FakeTransactionRepository:
    """A minimal in-memory stand-in for TransactionRepository.

    Used so these tests only depend on TransactionImportService
    (the file actually implemented in this commit) and not on
    TransactionRepository or TransactionInputForm, which are
    still stub files (separate issues).
    """

    def __init__(self):
        self.saved = []

    def save(self, transaction):
        self.saved.append(transaction)

    def find_by_category(self, category):
        return [t for t in self.saved if t.category == category]


def make_service():
    repo = FakeTransactionRepository()
    service = TransactionImportService(repository=repo)
    return service, repo


def test_manual_entry_saves_transaction():
    service, repo = make_service()

    service.import_manual_entry(amount=12.50, merchant="STARBUCKS", date="2026-09-26")

    assert len(repo.saved) == 1
    assert repo.saved[0].merchant == "STARBUCKS"
    assert repo.saved[0].amount == 12.50


def test_csv_upload_saves_multiple_transactions(tmp_path):
    service, repo = make_service()

    csv_path = tmp_path / "transactions.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["amount", "merchant", "date"])
        writer.writerow([20.00, "SHELL", "2026-09-25"])
        writer.writerow([9.99, "NETFLIX", "2026-09-24"])

    imported = service.import_csv(str(csv_path))

    assert len(imported) == 2
    assert len(repo.saved) == 2


def test_csv_upload_returns_transaction_objects_with_correct_amounts(tmp_path):
    service, repo = make_service()

    csv_path = tmp_path / "transactions.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["amount", "merchant", "date"])
        writer.writerow([45.67, "AMAZON", "2026-09-20"])

    imported = service.import_csv(str(csv_path))

    assert imported[0].amount == 45.67
    assert imported[0].merchant == "AMAZON"


def test_csv_upload_skips_malformed_row_instead_of_crashing(tmp_path):
    service, repo = make_service()

    csv_path = tmp_path / "transactions.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["amount", "merchant", "date"])
        writer.writerow(["not_a_number", "BAD ROW", "2026-09-20"])  # malformed
        writer.writerow([10.00, "GOOD ROW", "2026-09-20"])  # valid

    imported = service.import_csv(str(csv_path))

    assert len(imported) == 1
    assert imported[0].merchant == "GOOD ROW"
