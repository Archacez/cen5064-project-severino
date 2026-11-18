from budgeter.config import DATABASE_PATH
from budgeter.data.category_repository import CategoryRepository
from budgeter.data.transaction_repository import TransactionRepository
from budgeter.domain.transaction_categorization import TransactionCategorization
from budgeter.presentation.transaction_input_form import TransactionInputForm
from budgeter.service.transaction_import_service import TransactionImportService


def main():
    """Composition root: the one place that builds and connects the tiers."""
    categories = CategoryRepository(DATABASE_PATH)
    categories.seed_defaults()  # first run only; never overwrites the user's categories
    categorizer = TransactionCategorization(categories.find_all())
    service = TransactionImportService(TransactionRepository(DATABASE_PATH), categorizer=categorizer)
    TransactionInputForm(service).run()


if __name__ == "__main__":
    main()
