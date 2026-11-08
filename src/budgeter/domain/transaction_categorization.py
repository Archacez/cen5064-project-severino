import re

UNCATEGORIZED = "Uncategorized"


class TransactionCategorization:
    """Assigns a category name to a transaction using merchant keywords.

    Rules: matching ignores case and matches whole words only ("shell" matches
    "SHELL OIL 1234" but not "Seashells"). Categories are tried in the order
    given, and the first match wins. No match gives "Uncategorized".
    """

    def __init__(self, categories):
        self._rules = [
            (
                category.name,
                [re.compile(rf"(?<![^\W\d_]){re.escape(word)}(?![^\W\d_])", re.IGNORECASE) for word in category.keywords],
            )
            for category in categories
        ]

    def categorize(self, transaction):
        for name, patterns in self._rules:
            if any(pattern.search(transaction.merchant) for pattern in patterns):
                return name
        return UNCATEGORIZED
