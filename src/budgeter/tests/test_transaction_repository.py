from budgeter.data.transaction_repository import TransactionRepository
from budgeter.domain.transaction import Transaction


def make_repo(tmp_path):
    return TransactionRepository(db_path=tmp_path / "test.db")


def test_save_then_find_all_returns_transaction_objects(tmp_path):
    repo = make_repo(tmp_path)

    repo.save(Transaction(amount=12.5, merchant="STARBUCKS", date="2026-10-01"))

    results = repo.find_all()
    assert len(results) == 1
    assert isinstance(results[0], Transaction)
    assert results[0].amount == 12.5
    assert results[0].merchant == "STARBUCKS"
    assert results[0].date == "2026-10-01"
    assert results[0].category is None


def test_data_persists_across_repository_instances(tmp_path):
    TransactionRepository(db_path=tmp_path / "test.db").save(
        Transaction(amount=20.0, merchant="SHELL", date="2026-10-02")
    )

    reopened = TransactionRepository(db_path=tmp_path / "test.db")

    assert [t.merchant for t in reopened.find_all()] == ["SHELL"]


def test_find_by_category_filters_correctly(tmp_path):
    repo = make_repo(tmp_path)
    repo.save(Transaction(5.0, "STARBUCKS", "2026-10-01", category="Food"))
    repo.save(Transaction(40.0, "SHELL", "2026-10-02", category="Transport"))
    repo.save(Transaction(9.0, "MYSTERY", "2026-10-03"))

    assert [t.merchant for t in repo.find_by_category("Food")] == ["STARBUCKS"]
    assert [t.merchant for t in repo.find_by_category(None)] == ["MYSTERY"]
    assert repo.find_by_category("Nope") == []


def test_find_all_is_ordered_by_date(tmp_path):
    repo = make_repo(tmp_path)
    repo.save(Transaction(1.0, "LATER", "2026-10-09"))
    repo.save(Transaction(1.0, "EARLIER", "2026-10-01"))

    assert [t.merchant for t in repo.find_all()] == ["EARLIER", "LATER"]


def test_empty_repository_returns_empty_list(tmp_path):
    assert make_repo(tmp_path).find_all() == []


def test_merchant_with_quotes_is_stored_safely(tmp_path):
    repo = make_repo(tmp_path)
    nasty = "Bobby'); DROP TABLE transactions;--"

    repo.save(Transaction(1.0, nasty, "2026-10-01"))

    assert [t.merchant for t in repo.find_all()] == [nasty]
