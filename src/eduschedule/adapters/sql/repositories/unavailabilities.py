from __future__ import annotations
from sqlalchemy import select, and_
from datetime import datetime
from sqlalchemy.orm import Session
from eduschedule.domain.unavailability import Unavailability as domainUnavailability
from eduschedule.adapters.sql.models.unavailability import Unavailability as ormUnavailability
from eduschedule.adapters.sql.mappers import toDomainUnavailability

class UnavailabilityRepo:
    def __init__(self, s: Session):
        self.s = s
    
    def create(self, *, employeeId: int, startTime: datetime, endTime: datetime, note: str | None = None, allowOverlap: bool = True) -> domainUnavailability:
        if endTime <= startTime:
            raise ValueError('End time must be before start time.')
        
        if allowOverlap and self.conflicts(employeeId, startTime, endTime):
            raise ValueError('Interval overlaps with existing unavailability')
        oUnavailability = ormUnavailability(employee_id=employeeId, start_utc=startTime, end_utc=endTime, note=note)
        self.s.add(oUnavailability)
        self.s.flush()
        return toDomainUnavailability(oUnavailability)
    
    def viewUnavailabilities(self, employeeId: int):
        unv = self.s.scalars(select(ormUnavailability)
                             .where(ormUnavailability.employee_id == employeeId)
                             .order_by(ormUnavailability.start_utc)
                            )
        return [toDomainUnavailability(i) for i in unv]
    
    def conflicts(self, employeeId: int, startTime: datetime, endTime: datetime) -> bool:
        test = (select(ormUnavailability).where(and_(ormUnavailability.employee_id == employeeId,
                ormUnavailability.start_utc < endTime, ormUnavailability.end_utc > startTime)).limit(1))
        return self.s.scalar(test) is not None
    
    def delete(self, unavailabilityId: int) -> int:
        unv = self.s.get(ormUnavailability, unavailabilityId)
        if not unv:
            return 0
        self.s.delete(unv)
        return 1