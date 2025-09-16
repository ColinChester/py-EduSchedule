from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Schedule:
    id: int | None
    employeeId: int
    startUTC: datetime
    endUTC: datetime
