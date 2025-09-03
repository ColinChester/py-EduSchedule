from sqlalchemy.exc import IntegrityError
from eduschedule.adapters.sql.repositories.employees import EmployeeRepo
from eduschedule.adapters.sql.repositories.unavailabilities import UnavailabilityRepo
from eduschedule.adapters.sql.mappers import updateRole
from datetime import datetime, timedelta, timezone

def testCreateFetch(session):
    repo = EmployeeRepo(session)
    emp = repo.create(name='Alex', email='alex@example.com', roleName='flexer')
    session.commit()
    
    emp = repo.getByEmail('alex@example.com')
    assert emp is not None
    assert emp.name == 'Alex'
    assert emp.role == 'flexer'
    assert emp.maxHours == 20
    assert emp.active is True

def testUniqueEmail(session):
    repo = EmployeeRepo(session)
    repo.create(name='C', email='abc', roleName='123')
    session.commit()
    try:
        repo.create(name='C', email='abc', roleName='123')
        session.commit()
        assert False, 'Expected IntegrityError for duplicate email'
    except IntegrityError:
        session.rollback()

def testCreateRoleRow(session):
    r = updateRole(session, "Bag-Chaser")
    session.commit()
    assert r.id is not None

def testCreateWithoutRole(session):
    repo = EmployeeRepo(session)
    emp = repo.create(name='Lee', email='123', roleName=None)
    session.commit()
    assert emp.role is None

    get = repo.getByEmail('123')
    assert get is not None
    assert get.role is None

def testListWithUnavailabilities(session):
    eRepo = EmployeeRepo(session)
    uRepo = UnavailabilityRepo(session)
    emp1 = eRepo.create(name="A", email="a@example.com", roleName="r1")
    emp2 = eRepo.create(name="B", email="b@example.com", roleName="r2")
    session.commit()

    start = datetime(2020, 1, 1, 12, 0, tzinfo=timezone.utc)
    uRepo.create(employeeId=emp1.id, startTime=start, endTime=start + timedelta(hours=1))
    uRepo.create(employeeId=emp2.id, startTime=start, endTime=start + timedelta(hours=2))
    session.commit()

    employees = eRepo.listWithUnavailabilities()
    by_id = {e.id: e for e in employees}

    assert len(by_id[emp1.id].unavailabilities) == 1
    assert by_id[emp1.id].unavailabilities[0].employeeId == emp1.id
    assert len(by_id[emp2.id].unavailabilities) == 1