import csv

import pytest

from budgeter.service.transaction_import_service import TransactionImportService


class FakeTransactionRepository:
    """In-memory stand-in so these tests only exercise the service."""

    def __init__(self):
        self.saved = []

    def save(self, transaction):
        self.saved.append(transaction)

    def find_all(self):
        return list(self.saved)


def make_service():
    repo = FakeTransactionRepository()
    return TransactionImportService(repository=repo), repo


def write_csv(path, rows, header=("amount", "merchant", "date")):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        if header:
            writer.writerow(header)
        writer.writerows(rows)


# ---- manual entry ----------------------------------------------------


def test_manual_entry_saves_transaction():
    service, repo = make_service()

    service.import_manual_entry(amount=12.50, merchant="STARBUCKS", date="2026-09-26")

    assert len(repo.saved) == 1
    assert repo.saved[0].merchant == "STARBUCKS"
    assert repo.saved[0].amount == 12.50


@pytest.mark.parametrize("bad_amount", [-10.0, 0, float("nan"), float("inf"), None])
def test_manual_entry_rejects_bad_amounts(bad_amount):
    service, repo = make_service()

    with pytest.raises(ValueError):
        service.import_manual_entry(amount=bad_amount, merchant="SHELL", date="2026-09-26")

    assert repo.saved == []


def test_manual_entry_rejects_empty_merchant():
    service, repo = make_service()

    with pytest.raises(ValueError):
        service.import_manual_entry(amount=10.0, merchant="  ", date="2026-09-26")

    assert repo.saved == []


@pytest.mark.parametrize("bad_date", ["", "not a date", "2026-02-30", "09/26/2026"])
def test_manual_entry_rejects_bad_dates(bad_date):
    service, repo = make_service()

    with pytest.raises(ValueError):
        service.import_manual_entry(amount=10.0, merchant="SHELL", date=bad_date)

    assert repo.saved == []


# ---- CSV import --------------------------------------------------------


def test_csv_upload_saves_multiple_transactions(tmp_path):
    service, repo = make_service()
    path = tmp_path / "t.csv"
    write_csv(path, [[20.00, "SHELL", "2026-09-25"], [9.99, "NETFLIX", "2026-09-24"]])

    result = service.import_csv(str(path))
    imported = result.imported

    assert len(imported) == 2
    assert len(repo.saved) == 2
    assert result.skipped == 0


def test_csv_upload_parses_fields_correctly(tmp_path):
    service, _ = make_service()
    path = tmp_path / "t.csv"
    write_csv(path, [[45.67, "AMAZON", "2026-09-20"]])

    imported = service.import_csv(str(path)).imported

    assert imported[0].amount == 45.67
    assert imported[0].merchant == "AMAZON"
    assert imported[0].date == "2026-09-20"


def test_csv_upload_skips_malformed_amount_and_keeps_valid_row(tmp_path):
    service, _ = make_service()
    path = tmp_path / "t.csv"
    write_csv(
        path,
        [["not_a_number", "BAD ROW", "2026-09-20"], [10.00, "GOOD ROW", "2026-09-20"]],
    )

    result = service.import_csv(str(path))
    imported = result.imported

    assert [t.merchant for t in imported] == ["GOOD ROW"]
    assert result.skipped == 1


def test_csv_upload_skips_blank_merchant_instead_of_saving_nan(tmp_path):
    service, repo = make_service()
    path = tmp_path / "t.csv"
    write_csv(path, [[10.00, "", "2026-09-20"], [5.00, "   ", "2026-09-21"]])

    result = service.import_csv(str(path))
    imported = result.imported

    assert imported == []
    assert repo.saved == []
    assert result.skipped == 2


def test_csv_upload_skips_rows_with_bad_dates_or_non_positive_amounts(tmp_path):
    service, _ = make_service()
    path = tmp_path / "t.csv"
    write_csv(
        path,
        [
            [10.00, "BAD DATE", "yesterday"],
            [-5.00, "NEGATIVE", "2026-09-20"],
            [0, "ZERO", "2026-09-20"],
            [7.00, "OK", "2026-09-20"],
        ],
    )

    result = service.import_csv(str(path))
    imported = result.imported

    assert [t.merchant for t in imported] == ["OK"]
    assert result.skipped == 3


def test_csv_with_only_header_imports_nothing(tmp_path):
    service, repo = make_service()
    path = tmp_path / "t.csv"
    write_csv(path, [])

    assert service.import_csv(str(path)).imported == []
    assert repo.saved == []


def test_csv_with_all_rows_malformed_imports_nothing(tmp_path):
    service, repo = make_service()
    path = tmp_path / "t.csv"
    write_csv(path, [["x", "A", "2026-01-01"], ["y", "B", "2026-01-01"]])

    result = service.import_csv(str(path))

    assert result.imported == []
    assert repo.saved == []
    assert result.skipped == 2


@pytest.mark.parametrize("dropped", ["amount", "merchant", "date"])
def test_csv_missing_a_column_raises_clear_error(tmp_path, dropped):
    service, repo = make_service()
    path = tmp_path / "t.csv"
    header = [c for c in ("amount", "merchant", "date") if c != dropped]
    write_csv(path, [["1", "2"]], header=header)

    with pytest.raises(ValueError, match="missing required column"):
        service.import_csv(str(path))

    assert repo.saved == []


def test_csv_that_is_completely_empty_raises_clear_error(tmp_path):
    service, _ = make_service()
    path = tmp_path / "empty.csv"
    path.write_text("")

    with pytest.raises(ValueError, match="empty"):
        service.import_csv(str(path))


def test_csv_header_names_are_case_and_space_tolerant(tmp_path):
    service, _ = make_service()
    path = tmp_path / "t.csv"
    write_csv(path, [[3.00, "LYFT", "2026-09-20"]], header=(" Amount", "MERCHANT ", "Date"))

    assert len(service.import_csv(str(path)).imported) == 1


def test_csv_keeps_merchants_that_pandas_would_treat_as_missing(tmp_path):
    service, _ = make_service()
    path = tmp_path / "t.csv"
    write_csv(
        path,
        [[1.00, "NA", "2026-10-01"], [2.00, "None", "2026-10-02"], [3.00, "0001", "2026-10-03"]],
    )

    result = service.import_csv(str(path))
    imported = result.imported

    assert [t.merchant for t in imported] == ["NA", "None", "0001"]
    assert result.skipped == 0


def test_csv_accepts_thousands_separators_but_not_european_decimals(tmp_path):
    service, _ = make_service()
    path = tmp_path / "t.csv"
    write_csv(
        path,
        [["1,234.50", "RENT", "2026-10-01"], ["12,5", "AMBIGUOUS", "2026-10-02"]],
    )

    result = service.import_csv(str(path))
    imported = result.imported

    assert [(t.merchant, t.amount) for t in imported] == [("RENT", 1234.50)]
    assert result.skipped == 1  # "12,5" is rejected, not misread as 125


def test_each_import_reports_its_own_skip_count(tmp_path):
    service, _ = make_service()
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    write_csv(first, [["bad", "X", "2026-10-01"], [1.00, "OK", "2026-10-01"]])
    write_csv(second, [[2.00, "ALSO OK", "2026-10-02"]])

    first_result = service.import_csv(str(first))
    second_result = service.import_csv(str(second))

    assert first_result.skipped == 1
    assert second_result.skipped == 0  # nothing carried over from the first import
    assert not hasattr(service, "last_skipped_count")
