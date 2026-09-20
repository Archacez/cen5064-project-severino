class Transaction:
    """Represents a single imported transaction."""

    def __init__(self, amount, merchant, date, category=None):
        self.amount = amount
        self.merchant = merchant
        self.date = date
        self.category = category