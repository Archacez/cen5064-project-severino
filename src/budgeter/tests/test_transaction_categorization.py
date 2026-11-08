import pytest

from budgeter.domain.category import Category
from budgeter.domain.transaction import Transaction
from budgeter.domain.transaction_categorization import TransactionCategorization


def tx(merchant):
    return Transaction(amount=10, merchant=merchant, date="2026-10-01")


CATEGORIES = [
    Category("Food", ["uber eats", "starbucks"]),
    Category("Transport", ["uber", "shell"]),
]


def test_matching_keyword_gives_its_category():
    assert TransactionCategorization(CATEGORIES).categorize(tx("STARBUCKS #1234")) == "Food"


def test_matching_ignores_case():
    categorizer = TransactionCategorization(CATEGORIES)

    assert categorizer.categorize(tx("sHeLl oil")) == "Transport"


def test_no_match_falls_back_to_uncategorized():
    assert TransactionCategorization(CATEGORIES).categorize(tx("MYSTERY SHOP")) == "Uncategorized"


def test_no_categories_at_all_gives_uncategorized():
    assert TransactionCategorization([]).categorize(tx("STARBUCKS")) == "Uncategorized"


def test_first_matching_category_wins():
    categorizer = TransactionCategorization(CATEGORIES)

    assert categorizer.categorize(tx("UBER EATS ORDER")) == "Food"  # Food is listed first
    assert categorizer.categorize(tx("UBER TRIP")) == "Transport"


def test_whole_words_only():
    categorizer = TransactionCategorization(CATEGORIES)

    assert categorizer.categorize(tx("Seashells Gift Shop")) == "Uncategorized"


def test_keywords_with_punctuation_still_match():
    categorizer = TransactionCategorization([Category("Food", ["7-eleven"])])

    assert categorizer.categorize(tx("7-ELEVEN STORE 22")) == "Food"


def test_category_cleans_its_keywords():
    category = Category("  Food ", ["  Starbucks ", "starbucks", "", "Publix"])

    assert category.name == "Food"
    assert category.keywords == ("starbucks", "publix")


def test_category_rejects_bad_input():
    with pytest.raises(ValueError, match="name"):
        Category("  ", ["a"])
    with pytest.raises(TypeError, match="not one string"):
        Category("Food", "starbucks")
    with pytest.raises(TypeError, match="Invalid keyword"):
        Category("Food", ["ok", 5])
