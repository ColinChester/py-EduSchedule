from typer.testing import CliRunner


def testEmployeeImport(cliEnv, tmp_path):
    from eduschedule.cli.main import app
    file = tmp_path / "emps.csv"
    file.write_text("name,email,role,max_hours\n"
        "Alice,alice@example.com,teacher,30\n"
        "Bob,bob@example.com,assistant,25\n")
    runner = CliRunner()
    result = runner.invoke(app, ["import-employees", str(file)], env=cliEnv)
    assert result.exit_code == 0, result.output