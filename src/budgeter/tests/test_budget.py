import pytest

from budgeter.domain.budget import Budget


def test_under_the_limit_is_not_over():
    assert Budget("Food", 100).is_over_limit(99.99) is False


def test_exactly_at_the_limit_is_not_over_but_has_reached_it():
    budget = Budget("Food", 100)

    assert budget.is_over_limit(100) is False
    assert budget.has_reached_limit(100) is True


def test_one_cent_over_the_limit_is_over():
    budget = Budget("Food", 100)

    assert budget.is_over_limit(100.01) is True
    assert budget.has_reached_limit(100.01) is True


def test_exactly_at_the_limit_despite_floating_point_noise():
    budget = Budget("Food", 0.30)

    assert 0.1 + 0.2 != 0.30  # the float sum is 0.30000000000000004
    assert budget.is_over_limit(0.1 + 0.2) is False
    assert budget.has_reached_limit(0.1 + 0.2) is True


def test_nothing_spent_has_not_reached_the_limit():
    budget = Budget("Food", 50)

    assert budget.is_over_limit(0) is False
    assert budget.has_reached_limit(0) is False


def test_budget_cleans_the_category_and_stores_the_limit_as_a_float():
    budget = Budget("  Food ", 100)

    assert budget.category == "Food"
    assert budget.limit == 100.0
    assert isinstance(budget.limit, float)


@pytest.mark.parametrize("bad_limit", [0, -5, float("nan"), float("inf"), None, "100", True])
def test_rejects_bad_limits(bad_limit):
    with pytest.raises(ValueError, match="Invalid limit"):
        Budget("Food", bad_limit)


@pytest.mark.parametrize("bad_category", ["", "   ", None, 7])
def test_rejects_bad_categories(bad_category):
    with pytest.raises(ValueError, match="category"):
        Budget(bad_category, 100)


@pytest.mark.parametrize("bad_spent", [-0.01, float("nan"), float("inf"), None, "5", True])
def test_rejects_bad_spent_amounts(bad_spent):
    budget = Budget("Food", 100)

    with pytest.raises(ValueError, match="Invalid spent"):
        budget.is_over_limit(bad_spent)
    with pytest.raises(ValueError, match="Invalid spent"):
        budget.has_reached_limit(bad_spent)
