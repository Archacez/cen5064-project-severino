import csv

import pytest

from budgeter.data.transaction_repository import TransactionRepository
from budgeter.service.transaction_import_service import TransactionImportService
from budgeter.presentation.transaction_input_form import TransactionInputForm


@pytest.fixture
def repo(tmp_path):
    db_path = tmp_path / "test.db"
    return TransactionRepository(db_path=str(db_path))


@pytest.fixture
def service(repo):
    return TransactionImportService(repository=repo)


@pytest.fixture
def form(service):
    return TransactionInputForm(import_service=service)


def test_manual_entry_saves_transaction(form, repo):
    form.submit_manual_entry(amount=12.50, merchant="STARBUCKS", date="2026-09-26")

    results = repo.find_by_category(None)
    assert len(results) == 1
    assert results[0][2] == "STARBUCKS"


def test_csv_upload_saves_multiple_transactions(tmp_path, form, repo):
    csv_path = tmp_path / "transactions.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["amount", "merchant", "date"])
        writer.writerow([20.00, "SHELL", "2026-09-25"])
        writer.writerow([9.99, "NETFLIX", "2026-09-24"])

    imported = form.submit_csv_upload(str(csv_path))

    assert len(imported) == 2
    results = repo.find_by_category(None)
    assert len(results) == 2


def test_csv_upload_returns_transaction_objects_with_correct_amounts(tmp_path, form):
    csv_path = tmp_path / "transactions.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["amount", "merchant", "date"])
        writer.writerow([45.67, "AMAZON", "2026-09-20"])

    imported = form.submit_csv_upload(str(csv_path))

    assert imported[0].amount == 45.67
    assert imported[0].merchant == "AMAZON"


def test_csv_upload_skips_malformed_row_instead_of_crashing(tmp_path, form):
    csv_path = tmp_path / "transactions.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["amount", "merchant", "date"])
        writer.writerow(["not_a_number", "BAD ROW", "2026-09-20"])  # malformed
        writer.writerow([10.00, "GOOD ROW", "2026-09-20"])  # valid

    imported = form.submit_csv_upload(str(csv_path))

    assert len(imported) == 1
    assert imported[0].merchant == "GOOD ROW"
