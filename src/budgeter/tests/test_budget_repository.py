from budgeter.data.budget_repository import BudgetRepository
from budgeter.domain.budget import Budget


def make_repo(tmp_path):
    return BudgetRepository(db_path=tmp_path / "test.db")


def test_save_then_find_returns_a_budget_object(tmp_path):
    repo = make_repo(tmp_path)

    repo.save(Budget("Food", 250))

    found = repo.find_by_category("Food")
    assert isinstance(found, Budget)
    assert (found.category, found.limit) == ("Food", 250.0)


def test_budgets_survive_a_restart(tmp_path):
    make_repo(tmp_path).save(Budget("Transport", 80))

    reopened = make_repo(tmp_path)

    assert [(b.category, b.limit) for b in reopened.find_all()] == [("Transport", 80.0)]


def test_saving_again_replaces_the_limit(tmp_path):
    repo = make_repo(tmp_path)
    repo.save(Budget("Food", 250))
    repo.save(Budget("Food", 300))

    assert [b.limit for b in repo.find_all()] == [300.0]


def test_category_lookup_ignores_case(tmp_path):
    repo = make_repo(tmp_path)
    repo.save(Budget("Food", 250))
    repo.save(Budget("FOOD", 275))  # same category, different capitals

    assert len(repo.find_all()) == 1
    assert repo.find_by_category("food").limit == 275.0


def test_missing_budget_returns_none_and_empty_list_when_empty(tmp_path):
    repo = make_repo(tmp_path)

    assert repo.find_by_category("Food") is None
    assert repo.find_all() == []


def test_find_all_is_ordered_by_category(tmp_path):
    repo = make_repo(tmp_path)
    repo.save(Budget("Utilities", 100))
    repo.save(Budget("Food", 200))

    assert [b.category for b in repo.find_all()] == ["Food", "Utilities"]


def test_delete(tmp_path):
    repo = make_repo(tmp_path)
    repo.save(Budget("Food", 250))

    assert repo.delete("food") is True
    assert repo.delete("food") is False
    assert repo.find_all() == []
    
def test_sql_like_category_name_is_saved_as_data(tmp_path):
    repo = make_repo(tmp_path)
    unusual_name = "Food'; DROP TABLE budgets; --"

    repo.save(Budget(unusual_name, 100))

    found = repo.find_by_category(unusual_name)

    assert found.category == unusual_name
    assert found.limit == 100.0
    assert len(repo.find_all()) == 1