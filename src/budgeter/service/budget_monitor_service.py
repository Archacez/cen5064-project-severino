
from datetime import date


class BudgetMonitorService:
    """Evaluates category spending against saved budget limits."""

    def __init__(
        self,
        summary_service,
        budget_repository,
        warning_threshold=0.80,
    ):
        if not 0 < warning_threshold < 1:
            raise ValueError("Warning threshold must be between 0 and 1")

        self.summary_service = summary_service
        self.budget_repository = budget_repository
        self.warning_threshold = warning_threshold

    def get_budget_status(self, month=None):
        """Return spending progress and status for each saved budget."""
        if month is None:
            month = date.today().strftime("%Y-%m")

        spending = self.summary_service.spending_by_category(month)
        spending_by_category = {
            item["category"]: item["total"]
            for item in spending
        }

        budgets = self.budget_repository.find_all()
        results = []

        for budget in budgets:
            spent = spending_by_category.get(budget.category, 0.0)
            limit = budget.limit
            percentage_used = (spent / limit) * 100

            if budget.is_over_limit(spent):
                status = "over_limit"
            elif budget.has_reached_limit(spent):
                status = "limit_reached"
            elif percentage_used >= self.warning_threshold * 100:
                status = "approaching_limit"
            else:
                status = "within_budget"

            results.append(
                {
                    "category": budget.category,
                    "spent": spent,
                    "limit": limit,
                    "percentage_used": percentage_used,
                    "remaining": max(limit - spent, 0),
                    "status": status,
                }
            )

        return results
