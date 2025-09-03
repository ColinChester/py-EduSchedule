from eduschedule.adapters.sql.repositories.unavailabilities import UnavailabilityRepo
from eduschedule.adapters.sql.repositories.employees import EmployeeRepo
from datetime import datetime, timezone, timedelta

def testCreateFetch(session):
    emp = EmployeeRepo(session).create(name="", email="", roleName="test")
    session.commit()
    repo = UnavailabilityRepo(session)
    start = datetime(2020, 1, 1, 14, 0, tzinfo=timezone.utc)
    end = datetime(2020, 1, 1, 16, 0, tzinfo=timezone.utc)
    repo.create(employeeId=emp.id, startTime=start, endTime=end, note="Organization Meeting")
    session.commit()

    assert repo.conflicts(emp.id, start + timedelta(minutes=30), end + timedelta(minutes=30)) is True
    assert repo.conflicts(emp.id, end, end + timedelta(hours=1)) is False