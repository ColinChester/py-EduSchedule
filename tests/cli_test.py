from typer.testing import CliRunner
from datetime import datetime, timezone, timedelta
from eduschedule.adapters.sql.repositories.unavailabilities import UnavailabilityRepo
from eduschedule.adapters.sql.repositories.employees import EmployeeRepo
from eduschedule.adapters.sql.engine import session_scope
from eduschedule.cli.main import app

def testCLIDbInit(cliEnv):
    runner = CliRunner()
    result = runner.invoke(app, ['db-init'], env=cliEnv, catch_exceptions=False)
    assert result.exit_code == 0

def testAddUnavailabilityOverlap(cliEnv):
    runner = CliRunner()
    res = runner.invoke(app,["add-employee", "--name", "JohnDoe", "--email", "john@example.com","--role", "teacher",], env=cliEnv,)
    assert res.exit_code == 0, res.output
    res = runner.invoke(app,["add-unavailability", "--employeeid", "1", "--starttime", "2020-01-01 09:00", "--endtime", "2020-01-01 10:00",], env=cliEnv,)
    assert res.exit_code == 0

    # overlapping without flag should fail
    res = runner.invoke(app,["add-unavailability", "--employeeid", "1", "--starttime", "2020-01-01 09:30", "--endtime", "2020-01-01 10:30",], env=cliEnv,)
    assert res.exit_code != 0

    # allowing overlap should succeed
    res = runner.invoke(app,["add-unavailability", "--employeeid", "1", "--starttime", "2020-01-01 09:30", "--endtime", "2020-01-01 10:30", "--allow-overlap",], env=cliEnv,)
    assert res.exit_code == 0

def testlistUnavailabilitiesBetween(cliEnv):
    runner = CliRunner()
    with session_scope() as s:
        emp = EmployeeRepo(s).create(name="", email="", roleName="test")
        repo = UnavailabilityRepo(s)
        base = datetime(2020, 1, 1, 9, 0, tzinfo=timezone.utc)
        repo.create(employeeId=emp.id, startTime=base, endTime=base + timedelta(hours=1))
        repo.create(employeeId=emp.id, startTime=base + timedelta(hours=6), endTime=base + timedelta(hours=7))
        emp_id = emp.id
        result = runner.invoke(app,["list-unavailabilities", "--employee-id", str(emp_id), "--start-time", "2020-01-01 08:00", "--end-time", "2020-01-01 12:00", "--time-zone", "UTC",], env=cliEnv,)

    assert result.exit_code == 0, result.output
    assert "2020-01-01 09:00 -> 2020-01-01 10:00" in result.output
    assert "15:00" not in result.output