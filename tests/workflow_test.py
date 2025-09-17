from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from typer.testing import CliRunner

from eduschedule.adapters.sql.engine import session_scope
from eduschedule.adapters.sql.repositories.employees import EmployeeRepo
from eduschedule.adapters.sql.repositories.schedules import ScheduleRepo
from eduschedule.domain.scheduler import generate_schedule
from eduschedule.cli.main import app


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def test_end_to_end_workflow(cliEnv, tmp_path):
    runner = CliRunner()

    csv_path = tmp_path / "employees.csv"
    suffix = uuid4().hex[:8]
    alice_email = f"alice_{suffix}@example.com"
    bob_email = f"bob_{suffix}@example.com"
    csv_path.write_text(
        "name,email,role,max_hours\n"
        f"Alice,{alice_email},teacher,20\n"
        f"Bob,{bob_email},assistant,20\n"
    )

    result = runner.invoke(
        app, ["import-employees", str(csv_path)], env=cliEnv, catch_exceptions=False
    )
    assert result.exit_code == 0, result.output

    with session_scope() as s:
        employees = EmployeeRepo(s).list()
        by_email = {emp.email: emp for emp in employees}
        assert alice_email in by_email and bob_email in by_email
        alice = by_email[alice_email]
        bob = by_email[bob_email]
        assert alice.name == "Alice" and bob.name == "Bob"
        ids = {"Alice": alice.id, "Bob": bob.id}

    hour = timedelta(hours=1)
    start_0900 = datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc)
    start_1000 = start_0900 + hour
    start_1100 = start_1000 + hour
    start_1200 = start_1100 + hour

    for name, start, end, note in [
        ("Alice", start_0900, start_1000, "Team meeting"),
        ("Bob", start_1100, start_1200, "Doctor appointment"),
    ]:
        result = runner.invoke(
            app,
            [
                "add-unavailability",
                "--employeeid",
                str(ids[name]),
                "--starttime",
                _fmt(start),
                "--endtime",
                _fmt(end),
                "--time-zone",
                "UTC",
                "--note",
                note,
            ],
            env=cliEnv,
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output

    with session_scope() as s:
        employees = {emp.id: emp for emp in EmployeeRepo(s).listWithUnavailabilities()}
        assert len(employees[ids["Alice"]].unavailabilities) == 1
        assert len(employees[ids["Bob"]].unavailabilities) == 1

    preexisting_start = start_1000
    with session_scope() as s:
        ScheduleRepo(s).create(
            employeeId=ids["Bob"],
            startTime=preexisting_start,
            endTime=preexisting_start + hour,
        )

    target_ids = set(ids.values())

    with session_scope() as s:
        employees = [
            emp for emp in EmployeeRepo(s).listWithDetails() if emp.id in target_ids
        ]
        employees.sort(key=lambda emp: emp.id)
        assert {emp.id for emp in employees} == target_ids
        schedule_plan = generate_schedule(
            start_0900,
            start_1200,
            employees,
            slot_duration=hour,
        )
        expected_plan = [
            (ids["Bob"], start_0900, start_1000),
            (ids["Alice"], start_1000, start_1200),
        ]
        assert [
            (entry.employeeId, entry.startUTC, entry.endUTC)
            for entry in schedule_plan
        ] == expected_plan

        schedule_repo = ScheduleRepo(s)
        for entry in schedule_plan:
            schedule_repo.create(
                employeeId=entry.employeeId,
                startTime=entry.startUTC,
                endTime=entry.endUTC,
            )

    with session_scope() as s:
        schedule_repo = ScheduleRepo(s)
        alice_sched = schedule_repo.forEmployee(ids["Alice"])
        bob_sched = schedule_repo.forEmployee(ids["Bob"])

        assert [
            (item.startUTC, item.endUTC)
            for item in alice_sched
        ] == [(start_1000, start_1200)]
        assert [
            (item.startUTC, item.endUTC)
            for item in bob_sched
        ] == [
            (start_0900, start_1000),
            (start_1000, start_1100),
        ]

    with session_scope() as s:
        employees = {emp.id: emp for emp in EmployeeRepo(s).listWithDetails()}

    alice = employees[ids["Alice"]]
    bob = employees[ids["Bob"]]

    def _sorted(intervals):
        return sorted(intervals, key=lambda item: item.startUTC)

    assert [
        (item.startUTC, item.endUTC, item.note)
        for item in _sorted(alice.unavailabilities)
    ] == [(start_0900, start_1000, "Team meeting")]
    assert [
        (item.startUTC, item.endUTC, item.note)
        for item in _sorted(bob.unavailabilities)
    ] == [(start_1100, start_1200, "Doctor appointment")]

    assert [
        (item.startUTC, item.endUTC)
        for item in _sorted(alice.schedules)
    ] == [(start_1000, start_1200)]
    assert [
        (item.startUTC, item.endUTC)
        for item in _sorted(bob.schedules)
    ] == [
        (start_0900, start_1000),
        (start_1000, start_1100),
    ]
