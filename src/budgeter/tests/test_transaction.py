import pytest

from budgeter.domain.transaction import Transaction


def test_valid_transaction_is_created_and_cleaned():
    t = Transaction(amount=12, merchant="  Starbucks ", date=" 2026-10-01 ")

    assert t.amount == 12.0
    assert isinstance(t.amount, float)
    assert t.merchant == "Starbucks"
    assert t.date == "2026-10-01"
    assert t.category is None


@pytest.mark.parametrize(
    "bad_amount", [-10.0, 0, float("nan"), float("inf"), None, "12", True]
)
def test_rejects_bad_amounts(bad_amount):
    with pytest.raises(ValueError, match="Invalid amount"):
        Transaction(amount=bad_amount, merchant="SHELL", date="2026-10-01")


@pytest.mark.parametrize("bad_merchant", ["", "   ", None, 42])
def test_rejects_bad_merchants(bad_merchant):
    with pytest.raises(ValueError, match="Merchant"):
        Transaction(amount=5.0, merchant=bad_merchant, date="2026-10-01")


@pytest.mark.parametrize(
    "bad_date", ["", "not a date", "2026-02-30", "09/26/2026", "2026-9-5", None, 20261001]
)
def test_rejects_bad_dates(bad_date):
    with pytest.raises(ValueError, match="Invalid date"):
        Transaction(amount=5.0, merchant="SHELL", date=bad_date)
