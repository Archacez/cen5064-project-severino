
from budgeter.data.transaction_repository import TransactionRepository
from budgeter.domain.transaction import Transaction, TransactionType
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
    assert service.income_and_expenses() == {
        "income": 0.0,
        "expenses": 0.0,
        "net_cash_flow": 0.0,
    }

    assert service.monthly_cash_flow() == []

def test_income_expenses_and_monthly_cash_flow(tmp_path):
    repository = TransactionRepository(tmp_path / "cash_flow.db")

    # October transactions
    repository.save(
        Transaction(
            2000.00,
            "Employer",
            "2026-10-01",
            "Salary",
            TransactionType.INCOME,
        )
    )
    repository.save(
        Transaction(
            800.00,
            "Landlord",
            "2026-10-03",
            "Housing",
        )
    )

    # November transactions
    repository.save(
        Transaction(
            500.00,
            "Freelance Client",
            "2026-11-02",
            "Freelance",
            TransactionType.INCOME,
        )
    )
    repository.save(
        Transaction(
            100.00,
            "Chipotle",
            "2026-11-04",
            "Food",
        )
    )
    repository.save(
        Transaction(
            50.00,
            "Publix",
            "2026-11-05",
            "Food",
        )
    )
    repository.save(
        Transaction(
            100.00,
            "Gift",
            "2026-11-06",
            "Gifts",
            TransactionType.INCOME,
        )
    )

    service = SpendingSummaryService(repository)

    assert service.income_and_expenses() == {
        "income": 2600.00,
        "expenses": 950.00,
        "net_cash_flow": 1650.00,
    }

    assert service.monthly_cash_flow() == [
        {
            "month": "2026-10",
            "income": 2000.00,
            "expenses": 800.00,
            "net_cash_flow": 1200.00,
        },
        {
            "month": "2026-11",
            "income": 600.00,
            "expenses": 150.00,
            "net_cash_flow": 450.00,
        },
    ]

    assert service.spending_by_category() == [
        {"category": "Housing", "total": 800.00},
        {"category": "Food", "total": 150.00},
    ]