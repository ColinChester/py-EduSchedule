import csv
import os
import subprocess
import sys
from pathlib import Path
from sqlalchemy import select
import typer
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from eduschedule.adapters.sql.engine import session_scope
from eduschedule.adapters.sql.mappers import localToUTC
from eduschedule.adapters.sql.repositories.employees import EmployeeRepo
from eduschedule.adapters.sql.models.employee import Employee
from eduschedule.adapters.sql.repositories.unavailabilities import UnavailabilityRepo

app = typer.Typer(help="EduSchedule CLI")

@app.command("db-init")
def dbInit():
    result = subprocess.run(["alembic", "upgrade", "head"])
    if result.returncode != 0:
        typer.echo(
            "Alembic failed. Run 'alembic current/heads' to verify if DB schema is updated.",
            err=True,
        )
        sys.exit(result.returncode)
    typer.echo("Database migrated to head.")


@app.command(
    "add-employee",
    help="Enter first and last names as one argument with no spaces. Role and max_hours default to None and 20 respectively.",
)
def addEmployee(
    name: str = typer.Option(..., help="Full name, e.g. JohnDoe"),
    email: str = typer.Option(..., help="Email"),
    role: str | None = typer.Option(None, "--role", "-r", help="Role"),
    maxHours: int = typer.Option(20, "--max-hours", "-m", min=0, help="Max working hours/week"),
):
    if role is None or not role.strip():
        typer.secho("No role specified, will default to None.", fg="yellow")
        role = None

    with session_scope() as s:
        emp = EmployeeRepo(s).create(name=name, email=email, roleName=role, maxHours=maxHours)
        if emp.role is None:
            typer.echo(f"Created employee {emp.name}, ID: {emp.id}, email: {emp.email}, role: None")
        else:
            typer.echo(f"Created employee {emp.name}, ID: {emp.id}, email: {emp.email}, role: {emp.role}")

@app.command("add-unavailability")
def addUnavailability(
    employeeId: int = typer.Option(..., help="Employee ID (as it appears in the database)"),
    startTime: str = typer.Option(..., help="Unavailability start time, e.g. '2025-08-27 09:00'"),
    endTime: str = typer.Option(..., help="Unavailability end time"),
    timeZone: str = typer.Option("America/New_York", "--time-zone", "-z", help="Local timezone"),
    note: str | None = typer.Option(None, "--note", "-n", help="Note regarding unavailability (time off, sick, etc.)"),
    allowOverlap: bool = typer.Option(False, "--allow-overlap", "-o", help="prevents overlapping with existing availabilities (True/False)")
):
    with session_scope() as s:
        emp = s.scalar(select(Employee).where(Employee.id == employeeId))
        if not emp:
            _fail(f"Employee not found at employee ID: {employeeId}")
        
        startUTC = localToUTC(_parseLocalTime(startTime), timeZone)
        endUTC = localToUTC(_parseLocalTime(endTime), timeZone)
        
        unv = UnavailabilityRepo(s).create(employeeId=emp.id, startTime=startUTC, endTime=endUTC, note=note, checkOverlap=not allowOverlap)
        typer.echo(f'Created unavailability [{startTime} -> {endTime} tz: {timeZone}] (id: {unv.id}) for employee {emp.name} (id: {emp.id})')

@app.command("list-employees")
def listEmployees():
    with session_scope() as s:
        emps = EmployeeRepo(s).list()
        for e in emps:
            typer.echo(
                f"{e.id}\t{e.name}\t{e.email}\trole: {e.role}\tmax hours: {e.maxHours}"
            )

@app.command("list-unavailabilities")
def listUnavailabilities(
    employeeId: int = typer.Option(..., help="Employee ID (as it appears in the database)"),
    timeZone: str = typer.Option("America/New_York", "--time-zone", "-z", help="Local timezone"),
    startTime: str | None = typer.Option(None, "--start-time", "-st", help="Start of search range"),
    endTime: str | None = typer.Option(None, "--end-time", "-et", help="End of search range"),
):
    with session_scope() as s:
        emp = s.scalar(select(Employee).where(Employee.id == employeeId))
        if not emp:
            _fail(f"Employee not found at employee id: {employeeId}")
        if startTime and endTime:
            startUTC = localToUTC(_parseLocalTime(startTime), timeZone)
            endUTC = localToUTC(_parseLocalTime(endTime), timeZone)
            unvs = UnavailabilityRepo(s).listUnavailabilitiesBetween(startUTC, endUTC)
        elif startTime or endTime:
            _fail("Specify both start and end times")
        else:
            unvs = UnavailabilityRepo(s).viewUnavailabilities(employeeId)
        if not unvs:
            typer.echo("No unavailabilities found")
            return
        tz = ZoneInfo(timeZone)
        for i in unvs:
            startLocal = i.startUTC.astimezone(tz).strftime("%Y-%m-%d %H:%M")
            endLocal = i.endUTC.astimezone(tz).strftime("%Y-%m-%d %H:%M")
            typer.echo(f'{i.id}\t{startLocal} -> {endLocal}\tnote: {i.note}')

@app.command("parse-roles")
def parseRoles(
    csv_path: Path = typer.Argument(..., exists=True, readable=True, resolve_path=True)
):
    """Parse a CSV file mapping roles to employee names."""
    with csv_path.open(newline="") as f:
        reader = csv.reader(f)
        roles: dict[str, list[str]] = {}
        for row in reader:
            if not row:
                continue
            role, *names = row
            role = role.strip()
            if role.lower() == "role":
                continue
            cleaned = [n.strip() for n in names if n.strip()]
            roles.setdefault(role, []).extend(cleaned)
        for role, names in roles.items():
            typer.echo(f"{role}: {', '.join(names)}")



@app.command("import-employees", help="Import employees from a CSV file")
def importEmployees(
    csv_file: Path = typer.Argument(
        ..., exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True, help="CSV file path"
    )
):
    """Read employees from *csv_file* and add them to the database."""
    with csv_file.open(newline="") as fh, session_scope() as s:
        reader = csv.DictReader(fh)
        repo = EmployeeRepo(s)
        added = 0
        for row in reader:
            name = row.get("name")
            email = row.get("email")
            if not name or not email:
                continue
            role = row.get("role") or None
            max_hours_raw = row.get("max_hours") or row.get("maxHours")
            try:
                max_hours = int(max_hours_raw) if max_hours_raw else 20
            except ValueError:
                max_hours = 20
            repo.create(name=name, email=email, roleName=role, maxHours=max_hours)
            added += 1
    typer.echo(f"Imported {added} employees from {csv_file}")

@app.command("diagnostic")
def statsForNerds():
    from eduschedule.config import DATABASE_URL

    typer.echo(
        f'Package importable, Database URL: {os.getenv("DATABASE_URL", DATABASE_URL)}'
    )

def _parseLocalTime(time: str) -> datetime: # Format: YYYY-MM-DD HH:MM or YYYY-MM-DDTHH:MM
    time = time.replace("T", " ")
    dt = datetime.fromisoformat(time)
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        typer.secho('Parsed time without timezone, interpreting as local time', fg="yellow")
    return dt

def _fail(msg: str, code: int = 1):
    typer.secho(msg, fg='red', err=True)
    raise typer.Exit(code)

if __name__ == "__main__":
    app()
