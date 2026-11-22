
from budgeter.data.transaction_repository import TransactionRepository
from budgeter.domain.transaction import Transaction
from budgeter.service.transaction_import_service import TransactionImportService


def test_find_all_records_includes_database_id(tmp_path):
    repository = TransactionRepository(tmp_path / "test.db")
    repository.save(Transaction(25.50, "Publix", "2026-11-18"))

    records = repository.find_all_records()

    assert len(records) == 1
    assert records[0]["id"] == 1
    assert records[0]["merchant"] == "Publix"


def test_update_transaction(tmp_path):
    repository = TransactionRepository(tmp_path / "test.db")
    service = TransactionImportService(repository)

    service.import_manual_entry(25.50, "Publix", "2026-11-18")
    record = service.list_transaction_records()[0]

    updated = service.update_transaction(
        record["id"], 40.00, "Walmart", "2026-11-17"
    )

    assert updated is True

    result = service.list_transaction_records()[0]
    assert result["amount"] == 40.00
    assert result["merchant"] == "Walmart"
    assert result["date"] == "2026-11-17"


def test_delete_transaction(tmp_path):
    repository = TransactionRepository(tmp_path / "test.db")
    service = TransactionImportService(repository)

    service.import_manual_entry(25.50, "Publix", "2026-11-18")
    record = service.list_transaction_records()[0]

    assert service.delete_transaction(record["id"]) is True
    assert service.list_transaction_records() == []


def test_update_rejects_invalid_transaction(tmp_path):
    repository = TransactionRepository(tmp_path / "test.db")
    service = TransactionImportService(repository)

    service.import_manual_entry(25.50, "Publix", "2026-11-18")
    record = service.list_transaction_records()[0]

    try:
        service.update_transaction(
            record["id"], -10, "Walmart", "2026-11-17"
        )
        assert False, "Expected ValueError"
    except ValueError:
        pass
