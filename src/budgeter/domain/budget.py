import math
import numbers
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def _cents(amount):
    """Round to whole cents, so float noise like 0.1 + 0.2 equals 0.30."""
    return Decimal(str(amount)).quantize(CENT, rounding=ROUND_HALF_UP)


def _is_money(value):
    return (
        isinstance(value, numbers.Real)
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


class Budget:
    """A spending limit for one category.

    Rules: the limit is a positive amount, compared in whole cents.
    "Over the limit" means strictly more than the limit, so spending exactly
    AT the limit is not over. has_reached_limit() is true at the limit and above.
    """

    def __init__(self, category, limit):
        if not isinstance(category, str) or not category.strip():
            raise ValueError("Budget category cannot be empty")
        if not _is_money(limit) or limit <= 0:
            raise ValueError(f"Invalid limit: {limit!r} (must be a positive number)")
        self.category = category.strip()
        self.limit = float(limit)

    def is_over_limit(self, spent):
        return _cents(self._checked(spent)) > _cents(self.limit)

    def has_reached_limit(self, spent):
        return _cents(self._checked(spent)) >= _cents(self.limit)

    @staticmethod
    def _checked(spent):
        if not _is_money(spent) or spent < 0:
            raise ValueError(f"Invalid spent amount: {spent!r} (must be zero or more)")
        return spent
