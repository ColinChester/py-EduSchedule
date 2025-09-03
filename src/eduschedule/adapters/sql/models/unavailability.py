from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, String, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from eduschedule.adapters.sql.base import Base
from eduschedule.adapters.sql.models.employee import Employee
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .employee import Employee

class Unavailability(Base):
    __tablename__ = 'unavailabilities'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    
    start_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    employee: Mapped['Employee'] = relationship('Employee', back_populates="unavailabilities")
    
    __table_args__ = (CheckConstraint("end_utc > start_utc", name="ck_unavail_time_order"),
        Index("ix_unavail_emp_start_end", "employee_id", "start_utc", "end_utc"),)