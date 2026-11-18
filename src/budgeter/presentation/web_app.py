
import streamlit as st

from budgeter.config import DATABASE_PATH
from budgeter.data.category_repository import CategoryRepository
from budgeter.data.transaction_repository import TransactionRepository
from budgeter.domain.transaction_categorization import TransactionCategorization
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
    st.set_page_config(page_title="Budgeter", page_icon="💰", layout="wide")

    st.title("Budgeter")
    st.caption("Personal Finance and Expense Tracking")

    service = build_transaction_service()
    transactions = service.list_transactions()

    st.subheader("Your Transactions")

    if not transactions:
        st.info("No transactions found. Add transactions to get started.")
    else:
        transaction_data = [
            {
                "Date": transaction.date,
                "Merchant": transaction.merchant,
                "Category": transaction.category or "Uncategorized",
                "Amount": transaction.amount,
            }
            for transaction in transactions
        ]

        st.dataframe(
            transaction_data,
            use_container_width=True,
            hide_index=True,
        )

        total_spending = sum(t.amount for t in transactions)
        st.metric("Total Transactions", len(transactions))
        st.metric("Total Spending", f"${total_spending:,.2f}")


if __name__ == "__main__":
    main()
