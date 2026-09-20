class Category:
    """Represents a spending category with its matching keywords."""

    def __init__(self, name, keywords=None):
        self.name = name
        self.keywords = keywords or []