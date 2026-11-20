
import pytest

from budgeter.data.budget_repository import BudgetRepository
from budgeter.data.transaction_repository import TransactionRepository
from budgeter.domain.budget import Budget
from budgeter.domain.transaction import Transaction
from budgeter.service.budget_monitor_service import BudgetMonitorService
from budgeter.service.spending_summary_service import SpendingSummaryService


def create_budget_monitor(tmp_path):
    """Create budget monitoring dependencies using a temporary database."""
    db_path = tmp_path / "test.db"

    transaction_repository = TransactionRepository(db_path)
    budget_repository = BudgetRepository(db_path)

    summary_service = SpendingSummaryService(transaction_repository)

    return (
        transaction_repository,
        budget_repository,
        BudgetMonitorService(summary_service, budget_repository),
    )


@pytest.mark.parametrize(
    ("spent", "expected_status"),
    [
        (200, "within_budget"),
        (400, "approaching_limit"),
        (500, "limit_reached"),
        (550, "over_limit"),
    ],
)
def test_budget_statuses(tmp_path, spent, expected_status):
    transactions, budgets, monitor = create_budget_monitor(tmp_path)

    budgets.save(Budget("Food", 500))

    if spent > 0:
        transactions.save(
            Transaction(
                amount=spent,
                merchant="Grocery Store",
                date="2026-11-10",
                category="Food",
            )
        )

    results = monitor.get_budget_status("2026-11")

    assert len(results) == 1
    assert results[0]["category"] == "Food"
    assert results[0]["spent"] == spent
    assert results[0]["limit"] == 500
    assert results[0]["status"] == expected_status


def test_budget_status_with_no_spending(tmp_path):
    _, budgets, monitor = create_budget_monitor(tmp_path)

    budgets.save(Budget("Food", 500))

    results = monitor.get_budget_status("2026-11")

    assert results[0]["spent"] == 0
    assert results[0]["percentage_used"] == 0
    assert results[0]["remaining"] == 500
    assert results[0]["status"] == "within_budget"


def test_budget_status_only_counts_selected_month(tmp_path):
    transactions, budgets, monitor = create_budget_monitor(tmp_path)

    budgets.save(Budget("Food", 500))

    transactions.save(
        Transaction(200, "Grocery Store", "2026-11-10", "Food")
    )
    transactions.save(
        Transaction(300, "Grocery Store", "2026-10-10", "Food")
    )

    results = monitor.get_budget_status("2026-11")

    assert results[0]["spent"] == 200
    assert results[0]["percentage_used"] == 40
    assert results[0]["status"] == "within_budget"


def test_budget_status_excludes_income(tmp_path):
    transactions, budgets, monitor = create_budget_monitor(tmp_path)

    budgets.save(Budget("Food", 500))

    transactions.save(
        Transaction(200, "Grocery Store", "2026-11-10", "Food")
    )
    transactions.save(
        Transaction(
            3000,
            "Employer",
            "2026-11-10",
            "Food",
            transaction_type="income",
        )
    )

    results = monitor.get_budget_status("2026-11")

    assert results[0]["spent"] == 200
    assert results[0]["status"] == "within_budget"
