
from collections import defaultdict
from datetime import date


class SpendingSummaryService:
    """Calculates spending summaries from saved transaction records."""

    def __init__(self, repository):
        self.repository = repository

    def spending_by_category(self):
        """Return total spending grouped by category."""
        totals = defaultdict(float)

        for transaction in self.repository.find_all_records():
            category = transaction["category"] or "Uncategorized"
            totals[category] += transaction["amount"]

        return [
            {"category": category, "total": total}
            for category, total in sorted(
                totals.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ]

    def spending_by_month(self):
        """Return total spending grouped by month, chronologically."""
        totals = defaultdict(float)

        for transaction in self.repository.find_all_records():
            transaction_date = date.fromisoformat(transaction["date"])
            month = transaction_date.strftime("%Y-%m")
            totals[month] += transaction["amount"]

        return [
            {"month": month, "total": totals[month]}
            for month in sorted(totals)
        ]
