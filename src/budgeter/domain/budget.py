class Budget:
    """Represents a budget limit for a category, with threshold
    and over-limit checks."""

    def __init__(self, category, limit):
        self.category = category
        self.limit = limit

    def is_over_limit(self, spent_amount):
        pass