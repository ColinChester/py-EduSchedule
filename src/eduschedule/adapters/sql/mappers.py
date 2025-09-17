from eduschedule.domain.employee import Employee as domainEmployee
from eduschedule.adapters.sql.models.employee import Employee as ormEmployee, Role as roleObject
from eduschedule.domain.unavailability import Unavailability as domainUnavailability
from eduschedule.adapters.sql.models.unavailability import Unavailability as ormUnavailability
from eduschedule.domain.schedule import Schedule as domainSchedule
from eduschedule.adapters.sql.models.schedule import Schedule as ormSchedule
from sqlalchemy import select
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def toDomainEmployee(o: ormEmployee, *, withUnavailability: bool=False, withSchedules: bool=False) -> domainEmployee:
    unvs = [toDomainUnavailability(i) for i in o.unavailabilities] if withUnavailability else []
    schs = [toDomainSchedule(i) for i in o.schedules] if withSchedules else []
    role = o.role.name if o.role else None
    return domainEmployee(id=o.id, name=o.name, email=o.email, role=role, maxHours=o.max_hours, active=o.active, unavailabilities=unvs, schedules=schs)

def toDomainUnavailability(o: ormUnavailability) -> domainUnavailability:
    start = o.start_utc
    end = o.end_utc
    if start.tzinfo is None or start.tzinfo.utcoffset(start) is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None or end.tzinfo.utcoffset(end) is None:
        end = end.replace(tzinfo=timezone.utc)
    return domainUnavailability(
        id=o.id,
        employeeId=o.employee_id,
        startUTC=start,
        endUTC=end,
        note=o.note,
    )

def toDomainSchedule(o: ormSchedule) -> domainSchedule:
    start = o.start_utc
    end = o.end_utc
    if start.tzinfo is None or start.tzinfo.utcoffset(start) is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None or end.tzinfo.utcoffset(end) is None:
        end = end.replace(tzinfo=timezone.utc)
    return domainSchedule(id=o.id, employeeId=o.employee_id, startUTC=start, endUTC=end)

def updateRole(session, roleName: str | None) -> roleObject | None:
    if roleName is None or not roleName.strip():
        return None
    roleName = roleName.strip()
    role = session.scalar(select(roleObject).where(roleObject.name == roleName))
    if not role:
        role = roleObject(name=roleName)
        session.add(role)
        session.flush()
    return role

def localToUTC(localTime: datetime, timeZone: str) -> datetime:
    tz = ZoneInfo(timeZone)
    if localTime.tzinfo is None:
        localTime = localTime.replace(tzinfo=tz)
    return localTime.astimezone(timezone.utc)