from __future__ import annotations
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./eduschedule.db")
TZ_DEFAULT = os.getenv("TZ_DEFAULT", "America/New_York")