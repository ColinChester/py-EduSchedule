import csv
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

from eduschedule.adapters.sql.engine import session_scope
from eduschedule.adapters.sql.repositories.employees import EmployeeRepo

app = typer.Typer(help='EduSchedule CLI')

@app.command("db-init")
def dbInit():
    result = subprocess.run(['alembic', 'upgrade', 'head'])
    if result.returncode != 0:
        typer.echo("Alembic failed. Run 'alembic current/heads' to verify if DB schema is updated.", err=True)
        sys.exit(result.returncode)
    typer.echo("Database migrated to head.")
    
@app.command("add-employee", 
             help='Enter first and last names as one argument with no spaces. Role and max_hours default to None and 20 respectively.')
def addEmployee(
    name: str = typer.Option(..., help="Full name"),
    email: str = typer.Option(..., help="Email"),
    role: Optional[str] = typer.Option(None, "--role", "-r", help="Role"),
    maxHours: int = typer.Option(20, "--max-hours", "-m", min=0, help="Max working hours/week"),
    ):
    with session_scope() as s:
        emp = EmployeeRepo(s).create(name=name, email=email, roleName=role, maxHours=maxHours)
        typer.echo(f'Created employee {emp.name}, {emp.role} id: {emp.id} email: {emp.email}')

@app.command("list-employees")
def listEmployees():
    with session_scope() as s:
        emps = EmployeeRepo(s).list()
        for e in emps:
            typer.echo(f'{e.id}\t{e.name}\t{e.email}\trole: {e.role}\tmax hours: {e.maxHours}')


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
    typer.echo(f'Package importable, Database URL: {os.getenv("DATABASE_URL", DATABASE_URL)}')

if __name__ == "__main__":
    app()