from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from .unavailability import Unavailability
from .schedule import Schedule
@dataclass
class Employee:
    id: int | None
    name: str
    email: str
    role: str
    maxHours: int
    active: bool = True
    unavailabilities: List[Unavailability] = field(default_factory=list)
    schedules: List[Schedule] = field(default_factory=list)
