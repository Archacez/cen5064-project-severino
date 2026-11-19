
from collections import defaultdict
from datetime import date


class SpendingSummaryService:
    """Calculates financial summaries from saved transaction records."""

    def __init__(self, repository):
        self.repository = repository

    def income_and_expenses(self):
        """Return total income, expenses, and net cash flow."""
        income = 0.0
        expenses = 0.0

        for transaction in self.repository.find_all_records():
            if transaction["transaction_type"] == "income":
                income += transaction["amount"]
            else:
                expenses += transaction["amount"]

        return {
            "income": income,
            "expenses": expenses,
            "net_cash_flow": income - expenses,
        }

    def spending_by_category(self):
        """Return expense totals grouped by category."""
        totals = defaultdict(float)

        for transaction in self.repository.find_all_records():
            if transaction["transaction_type"] != "expense":
                continue

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

    def monthly_cash_flow(self):
        """Return monthly income and expenses, chronologically."""
        totals = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})

        for transaction in self.repository.find_all_records():
            transaction_date = date.fromisoformat(transaction["date"])
            month = transaction_date.strftime("%Y-%m")

            if transaction["transaction_type"] == "income":
                totals[month]["income"] += transaction["amount"]
            else:
                totals[month]["expenses"] += transaction["amount"]

        return [
            {
                "month": month,
                "income": totals[month]["income"],
                "expenses": totals[month]["expenses"],
                "net_cash_flow": (
                    totals[month]["income"] - totals[month]["expenses"]
                ),
            }
            for month in sorted(totals)
        ]

    def spending_by_month(self):
        """Return total expenses grouped by month, chronologically."""
        totals = defaultdict(float)

        for transaction in self.repository.find_all_records():
            if transaction["transaction_type"] != "expense":
                continue

            transaction_date = date.fromisoformat(transaction["date"])
            month = transaction_date.strftime("%Y-%m")
            totals[month] += transaction["amount"]

        return [
            {"month": month, "total": totals[month]}
            for month in sorted(totals)
        ]
