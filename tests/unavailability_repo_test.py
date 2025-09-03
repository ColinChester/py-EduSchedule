from eduschedule.adapters.sql.repositories.unavailabilities import UnavailabilityRepo
from eduschedule.adapters.sql.repositories.employees import EmployeeRepo
from datetime import datetime, timezone, timedelta
import pytest
import sys

def testCreateFetch(session):
    emp = EmployeeRepo(session).create(name="", email="test@edu.com", roleName="test")
    session.commit()
    repo = UnavailabilityRepo(session)
    start = datetime(2020, 1, 1, 14, 0, tzinfo=timezone.utc)
    end = datetime(2020, 1, 1, 16, 0, tzinfo=timezone.utc)
    repo.create(employeeId=emp.id, startTime=start, endTime=end, note="Organization Meeting")
    session.commit()

    assert repo.conflicts(emp.id, start + timedelta(minutes=30), end + timedelta(minutes=30)) is True
    assert repo.conflicts(emp.id, end, end + timedelta(hours=1)) is False

def testOverlapFlag(session):
    emp = EmployeeRepo(session).create(name="Colin", email="colin@chester.com", roleName="test")
    session.commit()
    repo = UnavailabilityRepo(session)
    start = datetime(2020, 1, 1, 14, 0, tzinfo=timezone.utc)
    end = datetime(2020, 1, 1, 16, 0, tzinfo=timezone.utc)
    repo.create(employeeId=emp.id, startTime=start, endTime=end)
    session.commit()

    with pytest.raises(ValueError):
        repo.create(employeeId=emp.id, startTime=start + timedelta(hours=1), endTime=end + timedelta(hours=1), checkOverlap=True)
    repo.create(employeeId=emp.id, startTime=start + timedelta(hours=1), endTime=end + timedelta(hours=1), checkOverlap=False)

    assert len(repo.viewUnavailabilities(emp.id)) == 2

def testNaiveDatetime(session):
    emp = EmployeeRepo(session).create(name="test", email="12345", roleName="test")
    session.commit()
    repo = UnavailabilityRepo(session)
    aware = datetime(2020, 1, 1, 14, 0, tzinfo=timezone.utc)
    naive = datetime(2020, 1, 1, 16, 0)

    with pytest.raises(ValueError):
        repo.create(employeeId=emp.id, startTime=naive, endTime=aware)

    with pytest.raises(ValueError):
        repo.create(employeeId=emp.id, startTime=aware, endTime=naive)