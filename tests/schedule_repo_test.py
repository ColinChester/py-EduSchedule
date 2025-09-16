from datetime import datetime, timezone, timedelta
from datetime import datetime, timezone, timedelta
from datetime import datetime, timezone, timedelta
import pytest

from eduschedule.adapters.sql.repositories.employees import EmployeeRepo
from eduschedule.adapters.sql.repositories.unavailabilities import UnavailabilityRepo
from eduschedule.adapters.sql.repositories.schedules import ScheduleRepo


def test_create_and_list(session):
    emp = EmployeeRepo(session).create(name="A", email="a@a.com", roleName="r")
    session.commit()
    repo = ScheduleRepo(session)
    start = datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=2)
    repo.create(employeeId=emp.id, startTime=start, endTime=end)
    session.commit()
    scheds = repo.forEmployee(emp.id)
    assert len(scheds) == 1
    assert scheds[0].startUTC == start
    assert scheds[0].endUTC == end


def test_conflict_with_unavailability(session):
    emp = EmployeeRepo(session).create(name="B", email="b@b.com", roleName="r")
    session.commit()
    urepo = UnavailabilityRepo(session)
    unv_start = datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc)
    unv_end = unv_start + timedelta(hours=2)
    urepo.create(employeeId=emp.id, startTime=unv_start, endTime=unv_end)
    session.commit()

    repo = ScheduleRepo(session)
    with pytest.raises(ValueError):
        repo.create(employeeId=emp.id, startTime=unv_start + timedelta(minutes=30), endTime=unv_end + timedelta(hours=1))
    # outside unavailability
    repo.create(employeeId=emp.id, startTime=unv_end, endTime=unv_end + timedelta(hours=1))
    session.commit()
    assert len(repo.forEmployee(emp.id)) == 1


def test_conflict_with_existing_schedule(session):
    emp = EmployeeRepo(session).create(name="C", email="c@c.com", roleName="r")
    session.commit()
    repo = ScheduleRepo(session)
    start = datetime(2024, 1, 3, 8, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=2)
    repo.create(employeeId=emp.id, startTime=start, endTime=end)
    session.commit()
    with pytest.raises(ValueError):
        repo.create(employeeId=emp.id, startTime=start + timedelta(minutes=30), endTime=end + timedelta(hours=1))

