from click.testing import CliRunner

from eduschedule.cli.main import app
from eduschedule.adapters.sql.engine import session_scope
from eduschedule.adapters.sql.repositories.employees import EmployeeRepo


def test_import_employees(cliEnv, tmp_path):
    csv_file = tmp_path / "emps.csv"
    csv_file.write_text(
        "name,email,role,max_hours\n"
        "Alice,alice@example.com,teacher,30\n"
        "Bob,bob@example.com,assistant,25\n"
    )
    runner = CliRunner()
    result = runner.invoke(app, ["import-employees", str(csv_file)], env=cliEnv)
    assert result.exit_code == 0, result.output
    with session_scope() as s:
        employees = EmployeeRepo(s).list()
        assert len(employees) == 2
        assert {e.name for e in employees} == {"Alice", "Bob"}
