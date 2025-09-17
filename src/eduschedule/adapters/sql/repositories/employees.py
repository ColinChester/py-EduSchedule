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
        self.s.commit()
        return toDomainEmployee(oEmployee)
    
    def getByEmail(self, email: str) -> domainEmployee | None:
        emp = self.s.scalar(select(ormEmployee).where(ormEmployee.email == email))
        return toDomainEmployee(emp) if emp else None

    def getById(self, id: int) -> domainEmployee | None:
        emp = self.s.scalar(select(ormEmployee).where(ormEmployee.id == id))
        return toDomainEmployee(emp) if emp else None
    
    def list(self) -> list[domainEmployee]:
        return self._list()

    def listWithUnavailabilities(self) -> list[domainEmployee]:
        return self._list(with_unavailability=True)

    def listWithDetails(self, *, active_only: bool = True) -> list[domainEmployee]:
        return self._list(with_unavailability=True, with_schedules=True, active_only=active_only)

    def _list(
        self,
        *,
        with_unavailability: bool = False,
        with_schedules: bool = False,
        active_only: bool = False,
    ) -> list[domainEmployee]:
        stmt = select(ormEmployee).order_by(ormEmployee.id)
        if active_only:
            stmt = stmt.where(ormEmployee.active.is_(True))
        if with_unavailability:
            stmt = stmt.options(selectinload(ormEmployee.unavailabilities))
        if with_schedules:
            stmt = stmt.options(selectinload(ormEmployee.schedules))
        emps = self.s.scalars(stmt).unique().all()
        return [
            toDomainEmployee(
                emp,
                withUnavailability=with_unavailability,
                withSchedules=with_schedules,
            )
            for emp in emps
        ]
