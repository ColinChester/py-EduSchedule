from __future__ import annotations
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from eduschedule.domain.schedule import Schedule as domainSchedule
from eduschedule.adapters.sql.models.schedule import Schedule as ormSchedule
from eduschedule.adapters.sql.models.unavailability import Unavailability as ormUnavailability
from eduschedule.adapters.sql.mappers import toDomainSchedule

class ScheduleRepo:
    def __init__(self, s: Session):
        self.s = s

    def create(self, *, employeeId: int, startTime: datetime, endTime: datetime, checkConflict: bool = True) -> domainSchedule:
        if startTime.tzinfo is None or startTime.tzinfo.utcoffset(startTime) is None:
            raise ValueError("startTime must be timezone-aware")
        if endTime.tzinfo is None or endTime.tzinfo.utcoffset(endTime) is None:
            raise ValueError("endTime must be timezone-aware")
        if endTime <= startTime:
            raise ValueError('End time must be before start time.')

        if checkConflict and (self.conflicts(employeeId, startTime, endTime) or self.unavailabilityConflict(employeeId, startTime, endTime)):
            raise ValueError('Interval conflicts with existing schedule or unavailability')
        oSchedule = ormSchedule(employee_id=employeeId, start_utc=startTime, end_utc=endTime)
        self.s.add(oSchedule)
        self.s.flush()
        return toDomainSchedule(oSchedule)

    def forEmployee(self, employeeId: int) -> list[domainSchedule]:
        scheds = self.s.scalars(select(ormSchedule).where(ormSchedule.employee_id == employeeId).order_by(ormSchedule.start_utc))
        return [toDomainSchedule(i) for i in scheds]

    def conflicts(self, employeeId: int, startTime: datetime, endTime: datetime) -> bool:
        stmt = select(ormSchedule).where(and_(ormSchedule.employee_id == employeeId, ormSchedule.start_utc < endTime, ormSchedule.end_utc > startTime)).limit(1)
        return self.s.scalar(stmt) is not None

    def unavailabilityConflict(self, employeeId: int, startTime: datetime, endTime: datetime) -> bool:
        stmt = select(ormUnavailability).where(and_(ormUnavailability.employee_id == employeeId, ormUnavailability.start_utc < endTime, ormUnavailability.end_utc > startTime)).limit(1)
        return self.s.scalar(stmt) is not None
