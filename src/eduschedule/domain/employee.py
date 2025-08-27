from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Employee:
    id: int | None
    name: str
    email: str
    role: str
    maxHours: int
    active: bool = True