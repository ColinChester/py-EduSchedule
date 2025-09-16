from datetime import datetime, timedelta, timezone

import pytest

from eduschedule.domain.employee import Employee
from eduschedule.domain.schedule import Schedule
from eduschedule.domain.unavailability import Unavailability
from eduschedule.domain.scheduler import generate_schedule, SchedulingError


def _make_employee(emp_id: int, **kwargs) -> Employee:
    base = dict(name=f"Employee {emp_id}", email=f"e{emp_id}@example.com", role="staff", maxHours=10)
    base.update(kwargs)
    return Employee(id=emp_id, **base)


def test_generate_schedule_balances_assignments():
    start = datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=4)
    employees = [_make_employee(1), _make_employee(2)]

    schedule = generate_schedule(start, end, employees)

    expected = [
        (1, start, start + timedelta(hours=1)),
        (2, start + timedelta(hours=1), start + timedelta(hours=2)),
        (1, start + timedelta(hours=2), start + timedelta(hours=3)),
        (2, start + timedelta(hours=3), end),
    ]
    assert [(s.employeeId, s.startUTC, s.endUTC) for s in schedule] == expected


def test_generate_schedule_respects_unavailability_and_merges():
    start = datetime(2024, 2, 5, 9, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=2)
    unavailable = Unavailability(
        id=1,
        employeeId=1,
        startUTC=start,
        endUTC=end,
        note=None,
    )
    employees = [
        _make_employee(1, unavailabilities=[unavailable]),
        _make_employee(2),
    ]

    schedule = generate_schedule(start, end, employees)

    assert len(schedule) == 1
    entry = schedule[0]
    assert entry.employeeId == 2
    assert entry.startUTC == start
    assert entry.endUTC == end


def test_generate_schedule_raises_when_capacity_exceeded():
    start = datetime(2024, 3, 1, 9, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=2)
    employees = [_make_employee(1, maxHours=1)]

    with pytest.raises(SchedulingError):
        generate_schedule(start, end, employees)


def test_generate_schedule_requires_timezone():
    start = datetime(2024, 4, 1, 9, 0)
    end = start + timedelta(hours=1)
    employees = [_make_employee(1)]

    with pytest.raises(ValueError):
        generate_schedule(start, end, employees)


def test_generate_schedule_handles_existing_schedule_conflicts():
    start = datetime(2024, 5, 1, 9, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=2)
    existing = Schedule(
        id=42,
        employeeId=1,
        startUTC=start,
        endUTC=start + timedelta(hours=1),
    )
    employees = [
        _make_employee(1, maxHours=3, schedules=[existing]),
        _make_employee(2, maxHours=3),
    ]

    schedule = generate_schedule(start, end, employees)

    expected = [
        (2, start, start + timedelta(hours=1)),
        (1, start + timedelta(hours=1), end),
    ]
    assert [(s.employeeId, s.startUTC, s.endUTC) for s in schedule] == expected
