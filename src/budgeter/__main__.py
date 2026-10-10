from budgeter.data.transaction_repository import TransactionRepository
from budgeter.presentation.transaction_input_form import TransactionInputForm
from budgeter.service.transaction_import_service import TransactionImportService


def main():
    """Composition root: the one place that builds and connects the tiers."""
    repository = TransactionRepository()
    service = TransactionImportService(repository)
    TransactionInputForm(service).run()


if __name__ == "__main__":
    main()
