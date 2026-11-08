import sqlite3

from budgeter.data.category_repository import DEFAULT_CATEGORIES, CategoryRepository
from budgeter.domain.category import Category


def make_repo(tmp_path):
    return CategoryRepository(db_path=tmp_path / "test.db")


def test_save_then_find_all_keeps_order_of_categories_and_keywords(tmp_path):
    repo = make_repo(tmp_path)
    repo.save(Category("Food", ["starbucks", "publix"]))
    repo.save(Category("Transport", ["shell", "uber"]))

    found = repo.find_all()

    assert [(c.name, c.keywords) for c in found] == [
        ("Food", ("starbucks", "publix")),
        ("Transport", ("shell", "uber")),
    ]
    assert all(isinstance(c, Category) for c in found)


def test_categories_survive_a_restart(tmp_path):
    make_repo(tmp_path).save(Category("Food", ["starbucks"]))

    assert [c.name for c in make_repo(tmp_path).find_all()] == ["Food"]


def test_saving_again_replaces_keywords_and_keeps_the_position(tmp_path):
    repo = make_repo(tmp_path)
    repo.save(Category("Food", ["starbucks"]))
    repo.save(Category("Transport", ["shell"]))
    repo.save(Category("food", ["publix", "cafe"]))  # same name, different case

    found = repo.find_all()

    assert [c.name for c in found] == ["Food", "Transport"]
    assert found[0].keywords == ("publix", "cafe")


def test_category_with_no_keywords_is_stored(tmp_path):
    repo = make_repo(tmp_path)
    repo.save(Category("Misc"))

    assert repo.find_by_name("misc").keywords == ()


def test_find_by_name_ignores_case_and_returns_none_when_missing(tmp_path):
    repo = make_repo(tmp_path)
    repo.save(Category("Food", ["starbucks"]))

    assert repo.find_by_name("FOOD").name == "Food"
    assert repo.find_by_name("Nope") is None


def test_delete_removes_the_category_and_its_keywords(tmp_path):
    repo = make_repo(tmp_path)
    repo.save(Category("Food", ["starbucks", "publix"]))

    assert repo.delete("food") is True
    assert repo.delete("food") is False
    assert repo.find_all() == []
    with sqlite3.connect(tmp_path / "test.db") as conn:
        assert conn.execute("SELECT COUNT(*) FROM category_keywords").fetchone()[0] == 0


def test_seed_defaults_fills_an_empty_table_once(tmp_path):
    repo = make_repo(tmp_path)

    assert repo.seed_defaults() is True
    assert repo.seed_defaults() is False
    assert [c.name for c in repo.find_all()] == [c.name for c in DEFAULT_CATEGORIES]


def test_seed_defaults_never_overwrites_the_users_own_categories(tmp_path):
    repo = make_repo(tmp_path)
    repo.save(Category("Pets", ["petco"]))

    assert repo.seed_defaults() is False
    assert [c.name for c in repo.find_all()] == ["Pets"]
