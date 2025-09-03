from sqlalchemy.exc import IntegrityError
from eduschedule.adapters.sql.repositories.employees import EmployeeRepo
from eduschedule.adapters.sql.mappers import updateRole

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