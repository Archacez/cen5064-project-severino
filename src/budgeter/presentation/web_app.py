import datetime

import streamlit as st

from budgeter.config import DATABASE_PATH
from budgeter.data.budget_repository import BudgetRepository
from budgeter.data.category_repository import CategoryRepository
from budgeter.data.transaction_repository import TransactionRepository
from budgeter.domain.budget import Budget
from budgeter.domain.transaction import TransactionType
from budgeter.domain.transaction_categorization import TransactionCategorization
from budgeter.presentation.dashboard import Dashboard
from budgeter.service.budget_monitor_service import BudgetMonitorService
from budgeter.service.spending_summary_service import SpendingSummaryService
from budgeter.service.transaction_import_service import TransactionImportService

INCOME_CATEGORIES = [
    "Salary",
    "Freelance",
    "Investments",
    "Gifts",
    "Benefits",
    "Other Income",
]


def build_services():
    """Build the repositories and services used by the web interface."""
    categories = CategoryRepository(DATABASE_PATH)
    categories.seed_defaults()

    transaction_repository = TransactionRepository(DATABASE_PATH)
    budget_repository = BudgetRepository(DATABASE_PATH)

    categorizer = TransactionCategorization(categories.find_all())

    transaction_service = TransactionImportService(
        transaction_repository,
        categorizer=categorizer,
    )

    summary_service = SpendingSummaryService(transaction_repository)

    budget_monitor = BudgetMonitorService(
        summary_service,
        budget_repository,
    )

    return transaction_service, summary_service, budget_monitor


def main():
    st.set_page_config(
        page_title="Budgeter",
        page_icon="💰",
        layout="wide",
    )

    st.title("💰 Budgeter")
    st.caption("Personal Finance and Expense Tracking")

    service, summary_service, budget_monitor = build_services()

    transactions = service.list_transaction_records()

    st.divider()

    dashboard_tab, view_tab, add_tab, manage_tab, budgets_tab = st.tabs(
        [
            "Dashboard",
            "View Transactions",
            "Add Transaction",
            "Manage Transactions",
            "Manage Budgets",
        ]
    )

    with dashboard_tab:
        Dashboard(summary_service, budget_monitor).render(transactions)

    with view_tab:
        st.subheader("Your Transactions")

        if transactions:
            st.dataframe(
                [
                    {
                        "Date": item["date"],
                        "Type": item["transaction_type"].capitalize(),
                        "Merchant": item["merchant"],
                        "Category": item["category"] or "Uncategorized",
                        "Amount": f"${item['amount']:,.2f}",
                    }
                    for item in transactions
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No transactions found. Add one to get started.")

    with add_tab:
        st.subheader("Add a Transaction")

        transaction_type = st.selectbox(
            "Transaction Type",
            options=[
                TransactionType.EXPENSE,
                TransactionType.INCOME,
            ],
            format_func=lambda item: item.value.capitalize(),
            key="add_transaction_type",
        )

        with st.form("add_transaction_form"):
            income_category = None

            if transaction_type == TransactionType.INCOME:
                income_category = st.selectbox(
                    "Income Category",
                    options=INCOME_CATEGORIES,
                )

            amount = st.number_input(
                "Amount ($)", min_value=0.01, step=1.0
            )
            merchant = st.text_input("Merchant")
            transaction_date = st.date_input(
                "Date", value=datetime.date.today()
            )

            submitted = st.form_submit_button("Save Transaction")

            if submitted:
                try:
                    service.import_manual_entry(
                        amount,
                        merchant,
                        transaction_date.isoformat(),
                        transaction_type=transaction_type,
                        category=income_category,
                    )
                    st.success("Transaction added successfully!")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

    with manage_tab:
        st.subheader("Edit or Delete a Transaction")

        if not transactions:
            st.info("There are no transactions to manage.")
        else:
            transaction_ids = [item["id"] for item in transactions]

            selected_id = st.selectbox(
                "Select a transaction",
                transaction_ids,
                format_func=lambda transaction_id: next(
                    (
                        f"{item['transaction_type'].capitalize()} - "
                        f"{item['merchant']} - "
                        f"${item['amount']:.2f} ({item['date']})"
                        for item in transactions
                        if item["id"] == transaction_id
                    ),
                    str(transaction_id),
                ),
            )

            selected = next(
                item for item in transactions
                if item["id"] == selected_id
            )

            new_transaction_type = st.selectbox(
                "Transaction Type",
                options=[
                    TransactionType.EXPENSE,
                    TransactionType.INCOME,
                ],
                index=(
                    0
                    if selected["transaction_type"] == "expense"
                    else 1
                ),
                format_func=lambda item: item.value.capitalize(),
                key=f"edit_type_{selected_id}",
            )

            with st.form("edit_transaction_form"):
                income_category = None

                if new_transaction_type == TransactionType.INCOME:
                    current_category = selected["category"]

                    default_index = (
                        INCOME_CATEGORIES.index(current_category)
                        if current_category in INCOME_CATEGORIES
                        else INCOME_CATEGORIES.index("Other Income")
                    )

                    income_category = st.selectbox(
                        "Income Category",
                        options=INCOME_CATEGORIES,
                        index=default_index,
                    )

                new_amount = st.number_input(
                    "Amount ($)",
                    min_value=0.01,
                    value=float(selected["amount"]),
                    step=1.0,
                )

                new_merchant = st.text_input(
                    "Merchant",
                    value=selected["merchant"],
                )

                new_date = st.date_input(
                    "Date",
                    value=datetime.date.fromisoformat(selected["date"]),
                )

                update_submitted = st.form_submit_button(
                    "Update Transaction"
                )

                if update_submitted:
                    try:
                        updated = service.update_transaction(
                            selected_id,
                            new_amount,
                            new_merchant,
                            new_date.isoformat(),
                            transaction_type=new_transaction_type,
                            category=income_category,
                        )

                        if updated:
                            st.success("Transaction updated successfully!")
                            st.rerun()
                        else:
                            st.error("Transaction could not be found.")
                    except ValueError as error:
                        st.error(str(error))

            st.divider()

            confirm_delete = st.checkbox(
                "I understand that deleting this transaction is permanent."
            )

            if st.button(
                "Delete Transaction",
                type="secondary",
                disabled=not confirm_delete,
            ):
                if service.delete_transaction(selected_id):
                    st.success("Transaction deleted successfully!")
                    st.rerun()
                else:
                    st.error("Transaction could not be found.")



    with budgets_tab:
        st.subheader("Manage Monthly Budgets")
        st.caption(
            "Set spending limits for your expense categories. "
            "Budgets remain saved until you change or delete them."
        )

        budget_repository = BudgetRepository(DATABASE_PATH)

        expense_categories = [
            category.name
            for category in CategoryRepository(DATABASE_PATH).find_all()
        ]

        saved_budgets = budget_repository.find_all()

        st.markdown("### Create or Update a Budget")

        if not expense_categories:
            st.info("No expense categories are available.")
        else:
            with st.form("add_budget_form"):
                selected_category = st.selectbox(
                    "Expense Category",
                    options=expense_categories,
                )

                existing_budget = next(
                    (
                        budget
                        for budget in saved_budgets
                        if budget.category.lower()
                        == selected_category.lower()
                    ),
                    None,
                )

                default_limit = (
                    existing_budget.limit
                    if existing_budget
                    else 100.00
                )

                budget_limit = st.number_input(
                    "Monthly Spending Limit ($)",
                    min_value=0.01,
                    value=float(default_limit),
                    step=10.0,
                )

                save_budget = st.form_submit_button(
                    "Save Budget"
                )

                if save_budget:
                    try:
                        budget = Budget(
                            selected_category,
                            budget_limit,
                        )

                        budget_repository.save(budget)

                        st.success(
                            f"Budget for {selected_category} saved successfully!"
                        )
                        st.rerun()

                    except ValueError as error:
                        st.error(str(error))

        st.divider()

        st.markdown("### Existing Budgets")

        saved_budgets = budget_repository.find_all()

        if not saved_budgets:
            st.info("You haven't created any budgets yet.")
        else:
            for budget in saved_budgets:
                budget_column, delete_column = st.columns(
                    [4, 1],
                    vertical_alignment="center",
                )

                with budget_column:
                    st.markdown(
                        f"**{budget.category}** — "
                        f"${budget.limit:,.2f} per month"
                    )

                with delete_column:
                    if st.button(
                        "Delete",
                        key=f"delete_budget_{budget.category}",
                    ):
                        budget_repository.delete(budget.category)
                        st.success(
                            f"{budget.category} budget deleted."
                        )
                        st.rerun()


if __name__ == "__main__":
    main()
