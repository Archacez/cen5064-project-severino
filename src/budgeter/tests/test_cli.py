from budgeter.data.transaction_repository import TransactionRepository
from budgeter.presentation.transaction_input_form import TransactionInputForm
from budgeter.service.transaction_import_service import TransactionImportService


def run_cli(db_path, typed_lines):
    """Run the real CLI -> service -> repository stack with scripted input."""
    lines = iter(typed_lines)
    output = []

    def fake_input(prompt):
        try:
            return next(lines)
        except StopIteration:
            raise EOFError from None  # what a real terminal does at end of input

    service = TransactionImportService(TransactionRepository(db_path=db_path))
    form = TransactionInputForm(service, input_fn=fake_input, output_fn=output.append)
    form.run()
    return "\n".join(output)


def test_manual_entry_end_to_end_and_persists_between_runs(tmp_path):
    db = tmp_path / "app.db"

    first = run_cli(db, ["1", "12.50", "STARBUCKS", "2026-10-01", "4"])
    assert "Transaction added." in first

    second = run_cli(db, ["3", "4"])  # brand new run, same database file
    assert "STARBUCKS" in second
    assert "12.50" in second


def test_csv_import_end_to_end_reports_counts(tmp_path):
    db = tmp_path / "app.db"
    csv_file = tmp_path / "t.csv"
    csv_file.write_text("amount,merchant,date\n5.00,LYFT,2026-10-01\nbad,X,2026-10-01\n")

    out = run_cli(db, ["2", str(csv_file), "3", "4"])

    assert "Imported 1 transaction(s). Skipped 1 invalid row(s)." in out
    assert "LYFT" in out


def test_bad_input_prints_message_and_does_not_crash(tmp_path):
    db = tmp_path / "app.db"

    not_a_number = run_cli(db, ["1", "abc", "4"])
    impossible_date = run_cli(db, ["1", "5", "SHELL", "13-45-2026", "4"])

    assert "Could not add transaction" in not_a_number
    assert "Could not add transaction" in impossible_date
    assert "No transactions yet." in run_cli(db, ["3", "4"])


def test_missing_csv_file_prints_message(tmp_path):
    out = run_cli(tmp_path / "app.db", ["2", str(tmp_path / "nope.csv"), "4"])

    assert "Could not read file" in out


def test_unknown_menu_choice_and_eof_are_handled(tmp_path):
    out = run_cli(tmp_path / "app.db", ["9"])  # input runs out -> EOFError path

    assert "Please enter 1, 2, 3 or 4." in out
    assert "Goodbye." in out
