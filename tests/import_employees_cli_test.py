import importlib
from contextlib import contextmanager


def test_import_employees_from_csv(tmp_path, monkeypatch):
    csv_path = tmp_path / "employees.csv"
    csv_path.write_text(
        "name,email,role,max_hours\n"
        "Alice,alice@example.com,teacher,25\n"
        "Bob,bob@example.com,assistant,30\n"
    )

    from eduschedule.cli import main as cli_main
    importlib.reload(cli_main)

    calls: list[tuple[str, str, str, int]] = []

    @contextmanager
    def fake_session_scope():
        yield None

    class FakeRepo:
        def __init__(self, s):
            pass

        def create(self, *, name: str, email: str, roleName: str | None, maxHours: int = 20):
            calls.append((name, email, roleName, maxHours))
            class _Emp:
                pass
            return _Emp()

    monkeypatch.setattr(cli_main, "session_scope", fake_session_scope)
    monkeypatch.setattr(cli_main, "EmployeeRepo", FakeRepo)

    cli_main.importEmployees(csv_path)

    assert calls == [
        ("Alice", "alice@example.com", "teacher", 25),
        ("Bob", "bob@example.com", "assistant", 30),
    ]

