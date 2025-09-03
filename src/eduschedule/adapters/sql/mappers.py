from eduschedule.domain.employee import Employee as domainEmployee
from eduschedule.adapters.sql.models.employee import Employee as ormEmployee, Role as roleObject
from eduschedule.domain.unavailability import Unavailability as domainUnavailability
from eduschedule.adapters.sql.models.unavailability import Unavailability as ormUnavailability
from sqlalchemy import select
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def toDomainEmployee(o: ormEmployee, *, withUnavailability: bool=False) -> domainEmployee:
    unvs = [toDomainUnavailability(i) for i in o.unavailabilities] if withUnavailability else []
    return domainEmployee(id=o.id, name=o.name, email=o.email, role=o.role.name, maxHours=o.max_hours, active=o.active, unavailabilities=unvs,)

def toDomainUnavailability(o: ormUnavailability) -> domainUnavailability:
    return domainUnavailability(
        id = o.id, employeeId = o.employee_id, startUTC = o.start_utc,
        endUTC = o.end_utc, note = o.note
    )

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