

import datetime

import streamlit as st

from budgeter.config import DATABASE_PATH
from budgeter.data.category_repository import CategoryRepository
from budgeter.data.transaction_repository import TransactionRepository
from budgeter.domain.transaction_categorization import TransactionCategorization
from budgeter.presentation.dashboard import Dashboard
from budgeter.service.spending_summary_service import SpendingSummaryService
from budgeter.service.transaction_import_service import TransactionImportService


def build_transaction_service():
    """Build the services and repositories used by the web interface."""
    categories = CategoryRepository(DATABASE_PATH)
    categories.seed_defaults()

    categorizer = TransactionCategorization(categories.find_all())

    return TransactionImportService(
        TransactionRepository(DATABASE_PATH),
        categorizer=categorizer,
    )


def main():
    st.set_page_config(
        page_title="Budgeter",
        page_icon="💰",
        layout="wide",
    )

    st.title("💰 Budgeter")
    st.caption("Personal Finance and Expense Tracking")

    service = build_transaction_service()
    transactions = service.list_transaction_records()

    summary_service = SpendingSummaryService(
    TransactionRepository(DATABASE_PATH)
    )

    transactions = service.list_transaction_records()
    summary_service = SpendingSummaryService(
        TransactionRepository(DATABASE_PATH)
        )

    st.divider()

    dashboard_tab, view_tab, add_tab, manage_tab = st.tabs(
        [
            "Dashboard",
            "View Transactions",
            "Add Transaction",
            "Manage Transactions",
        ]
    )

    with dashboard_tab:
        Dashboard(summary_service).render(transactions)

    with view_tab:
        st.subheader("Your Transactions")

        if transactions:
            st.dataframe(
                [
                    {
                        "Date": item["date"],
                        "Merchant": item["merchant"],
                        "Category": item["category"] or "Uncategorized",
                        "Amount": f"${item['amount']:.2f}",
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

        with st.form("add_transaction_form"):
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

            with st.form("edit_transaction_form"):
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


if __name__ == "__main__":
    main()
