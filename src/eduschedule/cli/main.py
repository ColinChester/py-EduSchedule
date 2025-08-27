import subprocess
import typer
from typing import Optional
import os
import sys
import csv
from pathlib import Path
from eduschedule.adapters.sql.engine import session_scope
from eduschedule.adapters.sql.repositories.employees import EmployeeRepo

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
    name: str = typer.Option(..., help="Full name"),
    email: str = typer.Option(..., help="Email"),
    role: Optional[str] = typer.Option(None, "--role", "-r", help="Role"),
    maxHours: int = typer.Option(
        20, "--max-hours", "-m", min=0, help="Max working hours/week"
    ),
):
    with session_scope() as s:
        emp = EmployeeRepo(s).create(
            name=name, email=email, roleName=role, maxHours=maxHours
        )
        typer.echo(
            f"Created employee {emp.name}, {emp.role} id: {emp.id} email: {emp.email}"
        )


@app.command("list-employees")
def listEmployees():
    with session_scope() as s:
        emps = EmployeeRepo(s).list()
        for e in emps:
            typer.echo(
                f"{e.id}\t{e.name}\t{e.email}\trole: {e.role}\tmax hours: {e.maxHours}"
            )


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


@app.command("diagnostic")
def statsForNerds():
    from eduschedule.config import DATABASE_URL

    typer.echo(
        f'Package importable, Database URL: {os.getenv("DATABASE_URL", DATABASE_URL)}'
    )


if __name__ == "__main__":
    app()
