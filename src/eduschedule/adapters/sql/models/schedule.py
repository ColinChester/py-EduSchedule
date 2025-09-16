from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from eduschedule.adapters.sql.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .employee import Employee

class Schedule(Base):
    __tablename__ = 'schedules'

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    start_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    employee: Mapped['Employee'] = relationship('Employee', back_populates='schedules')

    __table_args__ = (
        CheckConstraint("end_utc > start_utc", name="ck_sched_time_order"),
        Index("ix_sched_emp_start_end", "employee_id", "start_utc", "end_utc"),
    )
