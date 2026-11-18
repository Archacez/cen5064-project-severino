
from budgeter.data.transaction_repository import TransactionRepository
from budgeter.domain.transaction import Transaction
from budgeter.service.spending_summary_service import (
    SpendingSummaryService,
)


def test_spending_summaries_group_transactions_correctly(tmp_path):
    repository = TransactionRepository(tmp_path / "test.db")

    repository.save(
        Transaction(20.00, "Publix", "2026-10-05", "Food")
    )
    repository.save(
        Transaction(30.00, "Walmart", "2026-10-12", "Shopping")
    )
    repository.save(
        Transaction(15.00, "Chipotle", "2026-11-03", "Food")
    )
    repository.save(
        Transaction(10.00, "Unknown Store", "2026-11-08")
    )

    service = SpendingSummaryService(repository)

    assert service.spending_by_category() == [
        {"category": "Food", "total": 35.00},
        {"category": "Shopping", "total": 30.00},
        {"category": "Uncategorized", "total": 10.00},
    ]

    assert service.spending_by_month() == [
        {"month": "2026-10", "total": 50.00},
        {"month": "2026-11", "total": 25.00},
    ]


def test_spending_summaries_handle_empty_database(tmp_path):
    repository = TransactionRepository(tmp_path / "empty.db")
    service = SpendingSummaryService(repository)

    assert service.spending_by_category() == []
    assert service.spending_by_month() == []
