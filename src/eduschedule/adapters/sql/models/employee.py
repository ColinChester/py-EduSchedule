from __future__ import annotations
from sqlalchemy import String, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from eduschedule.adapters.sql.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .unavailability import Unavailability
    from .schedule import Schedule

class Role(Base):
    __tablename__ = 'roles'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    
    employees: Mapped[list['Employee']] = relationship(back_populates='role')
    
class Employee(Base):
    __tablename__ = 'employees'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    unavailabilities: Mapped[list['Unavailability']] = relationship('Unavailability', back_populates="employee", cascade="all, delete-orphan")
    schedules: Mapped[list['Schedule']] = relationship('Schedule', back_populates='employee', cascade="all, delete-orphan")
    max_hours: Mapped[int] = mapped_column(Integer, default=20)
    role: Mapped[Role] = relationship(back_populates="employees")
    
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"))
    
    __table_args__ = (UniqueConstraint('email', name='uq_emp_email'),)
