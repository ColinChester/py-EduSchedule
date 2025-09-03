from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from eduschedule.domain.employee import Employee as domainEmployee
from eduschedule.adapters.sql.models.employee import Employee as ormEmployee
from eduschedule.adapters.sql.mappers import toDomainEmployee, updateRole

class EmployeeRepo:
    def __init__(self, s: Session):
        self.s = s
    
    def create(self, *, name: str, email: str, roleName: str | None, maxHours: int=20) -> domainEmployee:
        role = updateRole(self.s, roleName)
        oEmployee = ormEmployee(name=name, email=email, max_hours=maxHours, active=True)
        if role is not None:
            oEmployee.role = role
        self.s.add(oEmployee)
        self.s.flush()
        return toDomainEmployee(oEmployee)
    
    def getByEmail(self, email: str) -> domainEmployee | None:
        emp = self.s.scalar(select(ormEmployee).where(ormEmployee.email == email))
        return toDomainEmployee(emp) if emp else None

    def getById(self, id: int) -> domainEmployee | None:
        emp = self.s.scalar(select(ormEmployee).where(ormEmployee.id == id))
        return toDomainEmployee(emp) if emp else None
    
    def list(self) -> list[domainEmployee]:
        return [toDomainEmployee(e) for e in self.s.scalars(select(ormEmployee)).all()]

    def listWithUnavailabilities(self) -> list[domainEmployee]:
        stmt = select(ormEmployee).options(selectinload(ormEmployee.unavailabilities))
        emps = self.s.scalars(stmt).unique().all()
        return [toDomainEmployee(i, withUnavailability=True) for i in emps]