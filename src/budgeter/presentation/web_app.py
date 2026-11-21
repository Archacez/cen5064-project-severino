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


    @st.dialog("Confirm Transaction Deletion")
    def confirm_transaction_delete(transaction):
        st.warning(
            f"Are you sure you want to delete "
            f"'{transaction['merchant']}' "
            f"(${transaction['amount']:,.2f})?"
        )

        st.caption("This action cannot be undone.")

        confirm_column, cancel_column = st.columns(2)

        with confirm_column:
            if st.button(
                "Confirm Delete",
                type="primary",
                width="stretch",
            ):
                if service.delete_transaction(transaction["id"]):
                    st.session_state.pop(
                        "selected_transaction_id", None
                    )
                    st.session_state.pop("transaction_action", None)
                    st.rerun()
                else:
                    st.error("Transaction could not be found.")

        with cancel_column:
            if st.button("Cancel", width="stretch",):
                st.session_state.pop(
                    "selected_transaction_id", None
                )
                st.session_state.pop("transaction_action", None)
                st.rerun()

    @st.dialog("Confirm Budget Deletion")
    def confirm_budget_delete(category):
        st.warning(
            f"Are you sure you want to delete the "
            f"{category} budget?"
        )
        st.caption("This action cannot be undone.")

        confirm_column, cancel_column = st.columns(2)

        with confirm_column:
            if st.button(
                "Confirm Delete",
                type="primary",
                width="stretch",
            ):
                budget_repository = BudgetRepository(DATABASE_PATH)
                budget_repository.delete(category)
                st.session_state.pop("selected_budget_category", None)
                st.rerun()

        with cancel_column:
            if st.button("Cancel", width="stretch"):
                st.session_state.pop("selected_budget_category", None)
                st.rerun()

    st.divider()

    dashboard_tab, manage_tab, budgets_tab = st.tabs(
        [
            "Dashboard",
            "Manage Transactions",
            "Manage Budgets",
        ]
    )

    with dashboard_tab:
        Dashboard(summary_service, budget_monitor).render(transactions)

    with manage_tab:
        st.subheader("Your Transactions")

        if transactions:
            for item in transactions:
                transaction_column, edit_column, delete_column = st.columns(
                    [6, 1, 1],
                    vertical_alignment="center",
                )

                with transaction_column:
                    transaction_type = item["transaction_type"].capitalize()
                    category = item["category"] or "Uncategorized"

                    st.markdown(
                        f"**{item['merchant']}** — "
                        f"${item['amount']:,.2f}"
                    )
                    st.caption(
                        f"{item['date']} · {category} · {transaction_type}"
                    )

                with edit_column:
                    if st.button(
                        "Edit",
                        key=f"edit_transaction_{item['id']}",
                        width="stretch",
                    ):
                        st.session_state["selected_transaction_id"] = item["id"]
                        st.session_state["transaction_action"] = "edit"
                        st.rerun()

                with delete_column:
                    if st.button(
                        "Delete",
                        key=f"delete_transaction_{item['id']}",
                        width="stretch",
                    ):
                        st.session_state["selected_transaction_id"] = item["id"]
                        st.session_state["transaction_action"] = "delete"
                        st.rerun()

                st.divider()
        else:
            st.info("No transactions found. Add one to get started.")

        
        if st.session_state.get("transaction_action") == "delete":
            selected_id = st.session_state.get("selected_transaction_id")

            selected_transaction = next(
                (
                    item for item in transactions
                    if item["id"] == selected_id
                ),
                None,
            )

            if selected_transaction:
                confirm_transaction_delete(selected_transaction)


    with manage_tab, st.expander("Add a Transaction", expanded=False):
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
        selected_id = st.session_state.get("selected_transaction_id")
        action = st.session_state.get("transaction_action")

        if selected_id and action == "edit":
            selected = next(
                (
                    item for item in transactions
                    if item["id"] == selected_id
                ),
                None,
            )

            if selected:
                st.subheader(f"Edit Transaction: {selected['merchant']}")

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

                with st.form(f"edit_transaction_form_{selected_id}"):
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
                                st.session_state.pop(
                                    "selected_transaction_id", None
                                )
                                st.session_state.pop("transaction_action", None)
                                st.rerun()
                            else:
                                st.error("Transaction could not be found.")

                        except ValueError as error:
                            st.error(str(error))

                if st.button("Cancel Editing"):
                    st.session_state.pop("selected_transaction_id", None)
                    st.session_state.pop("transaction_action", None)
                    st.rerun()



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
                        width="stretch",
                    ):
                        st.session_state["selected_budget_category"] = (
                            budget.category
                        )
                        st.rerun()
                        
        selected_budget = st.session_state.get(
            "selected_budget_category"
            )

        if selected_budget:
            confirm_budget_delete(selected_budget)


if __name__ == "__main__":
    main()
