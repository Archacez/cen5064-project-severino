import datetime
import math
import numbers
import re

ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


class Transaction:
    """A single spending record.

    The business rules live here, so a Transaction cannot be created
    in an invalid state no matter which path builds it (manual entry,
    CSV import, or reading rows back from the database).

    Rules: amount is a finite number greater than zero, merchant is
    non-empty text, date is a real calendar day written as YYYY-MM-DD.
    """

    def __init__(self, amount, merchant, date, category=None):
        self.amount = self._validate_amount(amount)
        self.merchant = self._validate_merchant(merchant)
        self.date = self._validate_date(date)
        self.category = category

    @staticmethod
    def _validate_amount(amount):
        is_number = isinstance(amount, numbers.Real) and not isinstance(amount, bool)
        if not is_number or not math.isfinite(amount) or amount <= 0:
            raise ValueError(f"Invalid amount: {amount!r} (must be a positive number)")
        return float(amount)

    @staticmethod
    def _validate_merchant(merchant):
        if not isinstance(merchant, str) or not merchant.strip():
            raise ValueError("Merchant cannot be empty")
        return merchant.strip()

    @staticmethod
    def _validate_date(date):
        text = date.strip() if isinstance(date, str) else None
        if text is not None and ISO_DATE.fullmatch(text):
            try:
                return datetime.date.fromisoformat(text).isoformat()
            except ValueError:
                pass  # right shape but not a real day, e.g. 2026-02-30
        raise ValueError(f"Invalid date: {date!r} (expected YYYY-MM-DD)")
