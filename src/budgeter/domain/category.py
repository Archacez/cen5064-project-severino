class Category:
    """A spending category and the merchant keywords that belong to it.

    Keywords are stored lower-case, trimmed, without blanks or repeats.
    The order of keywords is kept.
    """

    def __init__(self, name, keywords=None):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Category name cannot be empty")
        if isinstance(keywords, str):
            raise TypeError("keywords must be a list of words, not one string")
        self.name = name.strip()
        self.keywords = self._clean(keywords or [])

    @staticmethod
    def _clean(keywords):
        cleaned = []
        for word in keywords:
            if not isinstance(word, str):
                raise TypeError(f"Invalid keyword: {word!r}")
            word = word.strip().casefold()
            if word and word not in cleaned:
                cleaned.append(word)
        return tuple(cleaned)
