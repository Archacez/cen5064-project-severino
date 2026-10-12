MENU = """
=== Personal Finance Budgeter ===
1) Add a transaction
2) Import transactions from a CSV file
3) List transactions
4) Quit
"""


class TransactionInputForm:
    """Command-line interface for entering and viewing transactions.

    Contains no business rules and no SQL: it only collects input,
    calls TransactionImportService, and prints results. input_fn and
    output_fn can be swapped out so the form can be tested without a
    keyboard.
    """

    def __init__(self, import_service, input_fn=input, output_fn=print):
        self.service = import_service
        self.read = input_fn
        self.write = output_fn

    def run(self):
        try:
            while True:
                self.write(MENU)
                choice = self.read("Choose an option: ").strip()
                if choice == "1":
                    self.prompt_manual_entry()
                elif choice == "2":
                    self.prompt_csv_upload()
                elif choice == "3":
                    self.show_transactions()
                elif choice == "4":
                    break
                else:
                    self.write("Please enter 1, 2, 3 or 4.")
        except (EOFError, KeyboardInterrupt):
            pass
        self.write("Goodbye.")

    def prompt_manual_entry(self):
        try:
            amount = float(self.read("Amount: ").strip())
            merchant = self.read("Merchant: ")
            date = self.read("Date (YYYY-MM-DD): ")
            self.service.import_manual_entry(amount, merchant, date)
        except ValueError as error:
            self.write(f"Could not add transaction: {error}")
            return
        self.write("Transaction added.")

    def prompt_csv_upload(self):
        path = self.read("Path to CSV file: ").strip().strip('"')
        try:
            result = self.service.import_csv(path)
        except OSError as error:
            self.write(f"Could not read file: {error}")
            return
        except ValueError as error:
            self.write(f"Could not import CSV: {error}")
            return
        self.write(
            f"Imported {len(result.imported)} transaction(s). "
            f"Skipped {result.skipped} invalid row(s)."
        )

    def show_transactions(self):
        transactions = self.service.list_transactions()
        if not transactions:
            self.write("No transactions yet.")
            return
        for t in transactions:
            category = t.category or "Uncategorized"
            self.write(f"{t.date}  {t.amount:>10.2f}  {t.merchant}  [{category}]")
