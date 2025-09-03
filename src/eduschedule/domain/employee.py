from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from .unavailability import Unavailability
@dataclass
class Employee:
    id: int | None
    name: str
    email: str
    role: str
    maxHours: int
    active: bool = True
    unavailabilities: List[Unavailability] = field(default_factory=list)