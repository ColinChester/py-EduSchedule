from eduschedule.domain.employee import Employee as domainEmployee
from eduschedule.adapters.sql.models.employee import Employee as ormEmployee, Role as roleObject
from sqlalchemy import select

def toDomainEmployee(o: ormEmployee) -> domainEmployee:
    return domainEmployee(
        id = o.id, name = o.name, email = o.email,
        role = o.role.name,
        maxHours = o.max_hours, active = o.active
    )

def updateRole(session, roleName: str | None) -> roleObject | None:
    if roleName is None or not roleName.strip():
        raise ValueError("role_name must be a non-empty string")
    roleName = roleName.strip()
    role = session.scalar(select(roleObject).where(roleObject.name == roleName))
    if not role:
        role = roleObject(name=roleName)
        session.add(role)
        session.flush()
    return role