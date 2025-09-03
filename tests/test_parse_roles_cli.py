from typer.testing import CliRunner
from eduschedule.cli.main import app


def testParseRoles(tmp_path):
    csv_content = (
        "Role,Emp1,Emp2\nInstructor,Alice Smith,Bob Jones\nAssistant,Charlie Brown\n"
    )
    csv_file = tmp_path / "roles.csv"
    csv_file.write_text(csv_content)

    runner = CliRunner()
    result = runner.invoke(app, ["parse-roles", str(csv_file)])
    assert result.exit_code == 0
    assert "Instructor: Alice Smith, Bob Jones" in result.stdout
    assert "Assistant: Charlie Brown" in result.stdout
