from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, Sequence

from .employee import Employee
from .schedule import Schedule


class SchedulingError(ValueError):
    """Raised when a schedule cannot be generated for the given constraints."""


def generate_schedule(
    start: datetime,
    end: datetime,
    employees: Sequence[Employee],
    *,
    slot_duration: timedelta = timedelta(hours=1),
) -> list[Schedule]:
    """Generate schedules covering ``[start, end)``.

    The algorithm assigns employees to consecutive ``slot_duration`` windows while
    respecting the following constraints:

    * employees must be active and have available capacity (``maxHours``)
    * existing schedules and unavailabilities are treated as busy time
    * every slot must be handled by exactly one employee
    * assignments are balanced so the total workload stays evenly distributed

    The function returns a list of :class:`~eduschedule.domain.schedule.Schedule`
    objects (with ``id`` set to ``None``).  Consecutive slots assigned to the same
    employee are merged into a single schedule entry.
    """

    if not employees:
        raise ValueError("At least one employee is required to generate a schedule.")

    if not _is_timezone_aware(start) or not _is_timezone_aware(end):
        raise ValueError("start and end must be timezone-aware datetimes")

    for emp in employees:
        if emp.id is None:
            raise ValueError("All employees must have an id before scheduling")

    if end <= start:
        raise ValueError("end must be after start")

    if slot_duration <= timedelta(0):
        raise ValueError("slot_duration must be positive")

    total_duration = end - start
    if slot_duration > total_duration:
        slot_duration = total_duration

    busy_by_employee = [_build_busy_intervals(emp) for emp in employees]
    existing_seconds = [
        sum(_duration_seconds(s.startUTC, s.endUTC) for s in emp.schedules)
        for emp in employees
    ]
    assigned_seconds = [0.0] * len(employees)
    capacity_seconds = [
        max(0.0, float(emp.maxHours) * 3600.0 - existing)
        for emp, existing in zip(employees, existing_seconds, strict=True)
    ]
    assignments: list[list[tuple[datetime, datetime]]] = [[] for _ in employees]

    current_start = start
    order = list(range(len(employees)))

    while current_start < end:
        current_end = min(current_start + slot_duration, end)
        slot_seconds = _duration_seconds(current_start, current_end)

        candidates: list[int] = []
        for idx, emp in enumerate(employees):
            if not emp.active:
                continue
            if capacity_seconds[idx] - assigned_seconds[idx] < slot_seconds - 1e-9:
                continue
            if _has_conflict(busy_by_employee[idx], current_start, current_end):
                continue
            if _has_conflict(assignments[idx], current_start, current_end):
                continue
            candidates.append(idx)

        if not candidates:
            raise SchedulingError(
                "Unable to find an available employee for interval "
                f"{current_start.isoformat()} -> {current_end.isoformat()}"
            )

        chosen_idx = min(
            candidates,
            key=lambda i: (existing_seconds[i] + assigned_seconds[i], assigned_seconds[i], order[i]),
        )
        assignments[chosen_idx].append((current_start, current_end))
        assigned_seconds[chosen_idx] += slot_seconds
        current_start = current_end

    schedules: list[Schedule] = []
    for idx, emp_assignments in enumerate(assignments):
        if not emp_assignments:
            continue
        merged = _merge_intervals(emp_assignments)
        emp_id = employees[idx].id
        for start_time, end_time in merged:
            schedules.append(
                Schedule(
                    id=None,
                    employeeId=emp_id,
                    startUTC=start_time,
                    endUTC=end_time,
                )
            )

    schedules.sort(key=lambda s: s.startUTC)
    return schedules


def _is_timezone_aware(dt: datetime) -> bool:
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def _duration_seconds(start: datetime, end: datetime) -> float:
    return (end - start).total_seconds()


def _build_busy_intervals(emp: Employee) -> list[tuple[datetime, datetime]]:
    intervals: list[tuple[datetime, datetime]] = []
    for unv in emp.unavailabilities:
        if unv.startUTC < unv.endUTC:
            intervals.append((unv.startUTC, unv.endUTC))
    for sch in emp.schedules:
        if sch.startUTC < sch.endUTC:
            intervals.append((sch.startUTC, sch.endUTC))
    intervals.sort(key=lambda iv: iv[0])
    return intervals


def _has_conflict(
    intervals: Iterable[tuple[datetime, datetime]],
    start: datetime,
    end: datetime,
) -> bool:
    for busy_start, busy_end in intervals:
        if busy_start < end and busy_end > start:
            return True
    return False


def _merge_intervals(intervals: Iterable[tuple[datetime, datetime]]):
    merged: list[tuple[datetime, datetime]] = []
    for start, end in sorted(intervals, key=lambda iv: iv[0]):
        if not merged:
            merged.append((start, end))
            continue
        last_start, last_end = merged[-1]
        if start == last_end:
            merged[-1] = (last_start, end)
        else:
            merged.append((start, end))
    return merged
